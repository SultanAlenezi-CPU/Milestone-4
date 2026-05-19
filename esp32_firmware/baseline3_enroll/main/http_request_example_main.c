/* HTTP POST enrollment example using plain POSIX sockets
   Public Domain / CC0
*/
#include <string.h>
#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdlib.h>

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

#include "mbedtls/pk.h"
#include "mbedtls/ecp.h"
#include "mbedtls/x509_csr.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/entropy.h"

/* Target (update if needed) */
#define WEB_SERVER "172.20.10.4"
#define WEB_PORT   "8080"
#define WEB_PATH   "/enroll"

#define RUNS 5
#define GAP_MS 1500

#define CSR_BUF_SIZE  2048
#define JSON_BUF_SIZE 4096
#define BODY_BUF_SIZE 4608
#define REQ_BUF_SIZE  6144

static const char *TAG = "example";
static void json_escape_string(const char *src, char *dst, size_t dst_size);

static int generate_keypair(mbedtls_pk_context *key, mbedtls_ctr_drbg_context *ctr_drbg)
{
    int ret;

    mbedtls_pk_init(key);

    ret = mbedtls_pk_setup(key, mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
    if (ret != 0) {
        return ret;
    }

    ret = mbedtls_ecp_gen_key(
        MBEDTLS_ECP_DP_SECP256R1,
        mbedtls_pk_ec(*key),
        mbedtls_ctr_drbg_random,
        ctr_drbg);

    if (ret != 0) {
        mbedtls_pk_free(key);
    }

    return ret;
}

static int generate_csr(char *csr_buf, size_t buf_len)
{
    int ret;
    mbedtls_pk_context key;
    mbedtls_x509write_csr req;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;

    const char *pers = "csr";

    mbedtls_pk_init(&key);
    mbedtls_x509write_csr_init(&req);
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);

    ret = mbedtls_ctr_drbg_seed(
        &ctr_drbg,
        mbedtls_entropy_func,
        &entropy,
        (const unsigned char *)pers,
        strlen(pers));
    if (ret != 0) {
        goto cleanup;
    }

    ret = generate_keypair(&key, &ctr_drbg);
    if (ret != 0) {
        goto cleanup;
    }

    mbedtls_x509write_csr_set_key(&req, &key);
    mbedtls_x509write_csr_set_md_alg(&req, MBEDTLS_MD_SHA256);

    ret = mbedtls_x509write_csr_set_subject_name(&req, "CN=esp32_01");
    if (ret != 0) {
        goto cleanup;
    }

    ret = mbedtls_x509write_csr_pem(
        &req,
        (unsigned char *)csr_buf,
        buf_len,
        mbedtls_ctr_drbg_random,
        &ctr_drbg);

cleanup:
    mbedtls_x509write_csr_free(&req);
    mbedtls_pk_free(&key);
    mbedtls_ctr_drbg_free(&ctr_drbg);
    mbedtls_entropy_free(&entropy);

    return ret;
}

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

static void free_buffers(char *csr_buf, char *csr_json, char *body, char *request)
{
    free(csr_buf);
    free(csr_json);
    free(body);
    free(request);
}

static void http_enroll_task(void *pvParameters)
{
    const struct addrinfo hints = {
        .ai_family = AF_INET,
        .ai_socktype = SOCK_STREAM,
    };

    for (int run = 1; run <= RUNS; run++) {
        struct addrinfo *res = NULL;
        struct in_addr *addr = NULL;
        int s = -1, r = 0;
        int http_status = -1;

        char recv_buf[128];
        char *csr_buf = calloc(1, CSR_BUF_SIZE);
        char *csr_json = calloc(1, JSON_BUF_SIZE);
        char *body = calloc(1, BODY_BUF_SIZE);
        char *request = calloc(1, REQ_BUF_SIZE);

        if (csr_buf == NULL || csr_json == NULL || body == NULL || request == NULL) {
            ESP_LOGE(TAG, "Buffer allocation failed");
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        uint32_t heap_before = heap_caps_get_free_size(MALLOC_CAP_8BIT);
        int64_t t_start_us = esp_timer_get_time();

        printf("Generating CSR...\n");
        if (generate_csr(csr_buf, CSR_BUF_SIZE) == 0) {
            printf("CSR generated\n");
        } else {
            printf("CSR generation failed\n");
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        json_escape_string(csr_buf, csr_json, JSON_BUF_SIZE);

        int body_len = snprintf(body, BODY_BUF_SIZE,
                                "{\"run_id\":\"%d\",\"device_id\":\"esp32_01\",\"csr_pem\":\"%s\"}",
                                run, csr_json);
        if (body_len < 0 || body_len >= BODY_BUF_SIZE) {
            ESP_LOGE(TAG, "Body formatting failed");
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

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
            ESP_LOGE(TAG, "Request formatting failed");
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        int err = getaddrinfo(WEB_SERVER, WEB_PORT, &hints, &res);
        if (err != 0 || res == NULL) {
            ESP_LOGE(TAG, "DNS lookup failed err=%d res=%p", err, res);
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }

        addr = &((struct sockaddr_in *)res->ai_addr)->sin_addr;
        ESP_LOGI(TAG, "DNS lookup succeeded. IP=%s", inet_ntoa(*addr));

        s = socket(res->ai_family, res->ai_socktype, 0);
        if (s < 0) {
            ESP_LOGE(TAG, "... Failed to allocate socket.");
            freeaddrinfo(res);
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... allocated socket");

        if (connect(s, res->ai_addr, res->ai_addrlen) != 0) {
            ESP_LOGE(TAG, "... socket connect failed errno=%d", errno);
            close(s);
            freeaddrinfo(res);
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... connected");
        freeaddrinfo(res);

        if (send_all(s, request, (size_t)req_len) != 0) {
            ESP_LOGE(TAG, "... socket send failed errno=%d", errno);
            close(s);
            free_buffers(csr_buf, csr_json, body, request);
            vTaskDelay(pdMS_TO_TICKS(GAP_MS));
            continue;
        }
        ESP_LOGI(TAG, "... socket send success");

        struct timeval receiving_timeout = { .tv_sec = 15, .tv_usec = 0 };
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &receiving_timeout, sizeof(receiving_timeout));

        do {
            bzero(recv_buf, sizeof(recv_buf));
            r = read(s, recv_buf, sizeof(recv_buf) - 1);
            if (r > 0) {
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

        int64_t t_end_us = esp_timer_get_time();
        uint32_t heap_after = heap_caps_get_free_size(MALLOC_CAP_8BIT);

        int32_t heap_delta = (int32_t)heap_after - (int32_t)heap_before;
        uint32_t start_ms = (uint32_t)(t_start_us / 1000);
        uint32_t end_ms = (uint32_t)(t_end_us / 1000);
        uint32_t latency_ms = (uint32_t)((t_end_us - t_start_us) / 1000);
        int status = http_status;

        printf("MEASURE run_id=%d heap_before=%lu heap_after=%lu heap_delta=%ld start_ms=%" PRIu32 " end_ms=%" PRIu32 " latency_ms=%" PRIu32 " http_status=%d\n",
               run, (unsigned long)heap_before, (unsigned long)heap_after, (long)heap_delta,
               start_ms, end_ms, latency_ms, status);

        ESP_LOGI(TAG, "... done reading from socket. Last read return=%d errno=%d.", r, errno);
        close(s);

        free_buffers(csr_buf, csr_json, body, request);
        vTaskDelay(pdMS_TO_TICKS(GAP_MS));
    }

    ESP_LOGI(TAG, "MEASURE runs_done=%d", RUNS);
    vTaskDelete(NULL);
}

static void json_escape_string(const char *src, char *dst, size_t dst_size)
{
    size_t j = 0;

    for (size_t i = 0; src[i] != '\0' && j < dst_size - 2; i++) {

        if (src[i] == '\n') {
            dst[j++] = '\\';
            dst[j++] = 'n';
        }
        else if (src[i] == '\"') {
            dst[j++] = '\\';
            dst[j++] = '\"';
        }
        else if (src[i] == '\\') {
            dst[j++] = '\\';
            dst[j++] = '\\';
        }
        else {
            dst[j++] = src[i];
        }
    }

    dst[j] = '\0';
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    xTaskCreate(&http_enroll_task, "http_enroll_task", 8192, NULL, 5, NULL);
}



