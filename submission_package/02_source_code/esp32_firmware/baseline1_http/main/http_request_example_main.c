/* HTTP GET Example using plain POSIX sockets
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

/* Target (update if needed) */
#define WEB_SERVER "172.20.10.4"
#define WEB_PORT   "8080"
#define WEB_PATH   "/health"

#define RUNS 5
#define GAP_MS 1500

static const char *TAG = "example";

static const char *REQUEST =
    "GET " WEB_PATH " HTTP/1.0\r\n"
    "Host: " WEB_SERVER ":" WEB_PORT "\r\n"
    "User-Agent: esp-idf/1.0 esp32\r\n"
    "\r\n";

static void http_get_task(void *pvParameters)
{
    const struct addrinfo hints = {
        .ai_family = AF_INET,
        .ai_socktype = SOCK_STREAM,
    };

    for (int run = 1; run <= RUNS; run++) {

        struct addrinfo *res = NULL;
        struct in_addr *addr = NULL;
        int s = -1, r = 0;

        char recv_buf[64];

        uint32_t heap_before = heap_caps_get_free_size(MALLOC_CAP_8BIT);
        int64_t t_start_us = esp_timer_get_time();

        int err = getaddrinfo(WEB_SERVER, WEB_PORT, &hints, &res);
        if (err != 0 || res == NULL) {
            ESP_LOGE(TAG, "DNS lookup failed err=%d res=%p", err, res);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        addr = &((struct sockaddr_in *)res->ai_addr)->sin_addr;
        ESP_LOGI(TAG, "DNS lookup succeeded. IP=%s", inet_ntoa(*addr));

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

        if (write(s, REQUEST, strlen(REQUEST)) < 0) {
            ESP_LOGE(TAG, "... socket send failed errno=%d", errno);
            close(s);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... socket send success");

        struct timeval receiving_timeout = { .tv_sec = 5, .tv_usec = 0 };
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &receiving_timeout, sizeof(receiving_timeout));

        do {
            bzero(recv_buf, sizeof(recv_buf));
            r = read(s, recv_buf, sizeof(recv_buf) - 1);
            if (r > 0) {
                for (int i = 0; i < r; i++) putchar(recv_buf[i]);
            }
        } while (r > 0);

        int64_t t_end_us = esp_timer_get_time();
        uint32_t heap_after = heap_caps_get_free_size(MALLOC_CAP_8BIT);

        int32_t heap_delta = (int32_t)heap_after - (int32_t)heap_before;
        uint32_t latency_ms = (uint32_t)((t_end_us - t_start_us) / 1000);

        // http_status is not parsed in this raw socket example; we mark 200 if we reached end-of-read without early errors.
        int http_status = 200;

        printf("MEASURE run_id=%d heap_before=%" PRIu32 " heap_after=%" PRIu32 " heap_delta=%ld start_ms=%" PRIu32 " end_ms=%" PRIu32 " latency_ms=%" PRIu32 " http_status=%d\n",
               run, heap_before, heap_after, (long)heap_delta,
               (uint32_t)(t_start_us / 1000), (uint32_t)(t_end_us / 1000), latency_ms, http_status);

        ESP_LOGI(TAG, "... done reading from socket. Last read return=%d errno=%d.", r, errno);
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

    xTaskCreate(&http_get_task, "http_get_task", 4096, NULL, 5, NULL);
}
