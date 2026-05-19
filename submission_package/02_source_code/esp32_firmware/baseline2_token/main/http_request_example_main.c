/* HTTP POST Token Provisioning — Baseline 2 (QR/Token)
   Plain POSIX sockets, no TLS, no asymmetric crypto.
   Intentionally plaintext to demonstrate token-sniffing vulnerability.
   Public Domain / CC0
*/
#include <string.h>
#include <errno.h>
#include <inttypes.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_system.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "nvs_flash.h"
#include "protocol_examples_common.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"
#include "sdkconfig.h"

/* -----------------------------------------------------------------------
   Target — update with session IPs/port before building.
   Use scripts/handoff/update_b2_target.sh (or update manually).
   Direct to emulator:  WEB_SERVER = laptop IP, WEB_PORT = "5000"
   Via Pi relay:        WEB_SERVER = Pi IP,     WEB_PORT = "8080"
   ----------------------------------------------------------------------- */
#define WEB_SERVER "172.20.10.4"
#define WEB_PORT   "8080"
#define WEB_PATH   "/provision"

#define DEVICE_ID  "esp32_01"
#define RUNS       10
#define GAP_MS     1500

/* -----------------------------------------------------------------------
   Dev/test token array — 10 tokens, one consumed per run.
   These match the tokens in cloud_emulator/api/b2_tokens.example.json.
   Before a real session: copy b2_tokens.example.json -> b2_tokens.json,
   optionally replace with freshly generated tokens, and update this array
   to match.  See docs/b2_dev_tokens_and_first_run.md for the procedure.
   ----------------------------------------------------------------------- */
static const char *TOKENS[RUNS] = {
    "a3f9c2e1b8d4f7a2c0e5d9b3f1e8a6c4",  /* run 1  */
    "b2e8d1f4a7c3e9b0d5f2a1e7c4b9f3a2",  /* run 2  */
    "c1d7e3f9b4a2c8e5d0f1b6e4a3c9d7f2",  /* run 3  */
    "d4e6f8a2c0b3e1f9a7d5c2b8e3f1a4c6",  /* run 4  */
    "e5f7a9b1c3d0e2f8b6a4d1c7e9f3b5a7",  /* run 5  */
    "f6a8b0c2d4e3f7a1b9c5d8e0f2a6b4c8",  /* run 6  */
    "a7b9c1d3e5f4a0b8c6d9e2f1a3b7c5d0",  /* run 7  */
    "b8c0d2e4f6a5b1c9d7e3f0a2b4c6d8e1",  /* run 8  */
    "c9d1e3f5a7b6c2d0e8f4a1b3c5d7e9f2",  /* run 9  */
    "d0e2f4a6b8c7d3e1f9a5b2c4d6e8f0a3",  /* run 10 */
};

#define BODY_BUF_SIZE 192
#define REQ_BUF_SIZE  512
#define RECV_BUF_SIZE 256

static const char *TAG = "example";

static int send_all(int sock, const char *buf, size_t len)
{
    size_t sent = 0;
    while (sent < len) {
        int w = write(sock, buf + sent, len - sent);
        if (w < 0) {
            return -1;
        }
        sent += (size_t)w;
    }
    return 0;
}

static void http_provision_task(void *pvParameters)
{
    const struct addrinfo hints = {
        .ai_family   = AF_INET,
        .ai_socktype = SOCK_STREAM,
    };

    char body[BODY_BUF_SIZE];
    char request[REQ_BUF_SIZE];
    char recv_buf[RECV_BUF_SIZE];

    for (int run = 1; run <= RUNS; run++) {

        struct addrinfo *res = NULL;
        struct in_addr  *addr = NULL;
        int s = -1, r = 0;
        int http_status = -1;

        uint32_t heap_before = heap_caps_get_free_size(MALLOC_CAP_8BIT);
        int64_t  t_start_us  = esp_timer_get_time();

        /* Build JSON body */
        int body_len = snprintf(body, BODY_BUF_SIZE,
            "{\"run_id\":\"%d\",\"device_id\":\"%s\",\"token\":\"%s\"}",
            run, DEVICE_ID, TOKENS[run - 1]);
        if (body_len < 0 || body_len >= BODY_BUF_SIZE) {
            ESP_LOGE(TAG, "Body buffer too small for run %d", run);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        /* Build HTTP request */
        int req_len = snprintf(request, REQ_BUF_SIZE,
            "POST " WEB_PATH " HTTP/1.0\r\n"
            "Host: " WEB_SERVER ":" WEB_PORT "\r\n"
            "User-Agent: esp-idf/1.0 esp32\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: %d\r\n"
            "\r\n"
            "%s",
            body_len, body);
        if (req_len < 0 || req_len >= REQ_BUF_SIZE) {
            ESP_LOGE(TAG, "Request buffer too small for run %d", run);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        /* DNS */
        int err = getaddrinfo(WEB_SERVER, WEB_PORT, &hints, &res);
        if (err != 0 || res == NULL) {
            ESP_LOGE(TAG, "DNS lookup failed err=%d res=%p", err, res);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        addr = &((struct sockaddr_in *)res->ai_addr)->sin_addr;
        ESP_LOGI(TAG, "DNS lookup succeeded. IP=%s", inet_ntoa(*addr));

        /* Socket */
        s = socket(res->ai_family, res->ai_socktype, 0);
        if (s < 0) {
            ESP_LOGE(TAG, "... Failed to allocate socket.");
            freeaddrinfo(res);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... allocated socket");

        if (connect(s, res->ai_addr, res->ai_addrlen) != 0) {
            ESP_LOGE(TAG, "... socket connect failed errno=%d", errno);
            close(s);
            freeaddrinfo(res);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... connected");
        freeaddrinfo(res);

        /* Send */
        if (send_all(s, request, (size_t)req_len) != 0) {
            ESP_LOGE(TAG, "... socket send failed errno=%d", errno);
            close(s);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... socket send success");

        /* Receive — 8 s timeout; via-Pi relay occasionally exceeds 5 s on late runs */
        struct timeval receiving_timeout = { .tv_sec = 8, .tv_usec = 0 };
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &receiving_timeout,
                   sizeof(receiving_timeout));

        do {
            bzero(recv_buf, sizeof(recv_buf));
            r = read(s, recv_buf, sizeof(recv_buf) - 1);
            if (r > 0) {
                /* Parse HTTP status from first chunk */
                if (http_status < 0) {
                    int parsed = -1;
                    if (sscanf(recv_buf, "HTTP/%*d.%*d %d", &parsed) == 1) {
                        http_status = parsed;
                    }
                }
                for (int i = 0; i < r; i++) {
                    putchar(recv_buf[i]);
                }
            }
        } while (r > 0);

        int64_t  t_end_us   = esp_timer_get_time();
        uint32_t heap_after = heap_caps_get_free_size(MALLOC_CAP_8BIT);

        int32_t  heap_delta = (int32_t)heap_after - (int32_t)heap_before;
        uint32_t start_ms   = (uint32_t)(t_start_us / 1000);
        uint32_t end_ms     = (uint32_t)(t_end_us   / 1000);
        uint32_t latency_ms = (uint32_t)((t_end_us - t_start_us) / 1000);

        printf("MEASURE run_id=%d heap_before=%" PRIu32 " heap_after=%" PRIu32
               " heap_delta=%ld start_ms=%" PRIu32 " end_ms=%" PRIu32
               " latency_ms=%" PRIu32 " http_status=%d\n",
               run, heap_before, heap_after, (long)heap_delta,
               start_ms, end_ms, latency_ms, http_status);

        ESP_LOGI(TAG, "... done reading from socket. Last read return=%d errno=%d.",
                 r, errno);
        close(s);

        vTaskDelay(pdMS_TO_TICKS(GAP_MS));
    }

    ESP_LOGI(TAG, "MEASURE runs_done=%d", RUNS);
    vTaskDelete(NULL);
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    xTaskCreate(&http_provision_task, "http_provision_task", 4096, NULL, 5, NULL);
}
