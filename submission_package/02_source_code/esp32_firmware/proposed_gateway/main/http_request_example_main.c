/* Proposed Method — Gateway-Brokered Two-Phase Enrollment
   Plain POSIX sockets, no TLS, mbedTLS for EC keypair + CSR only.
   Intentionally plaintext to demonstrate that even two-phase auth
   is vulnerable to passive sniffing without transport security.
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

/* -----------------------------------------------------------------------
   Target — update with session IPs before building.
   Use scripts/handoff/update_b1_target.sh (or edit manually):
     WEB_SERVER = Pi IP
     WEB_PORT   = "8090"  (proposed gateway port, NOT dumb relay 8080)
   ----------------------------------------------------------------------- */
#define WEB_SERVER    "172.20.10.4"
#define WEB_PORT      "8090"
#define AUTH_PATH     "/gateway/auth"
#define ENROLL_PATH   "/gateway/enroll"

#define DEVICE_ID     "esp32_01"
#define DEVICE_TOKEN  "proposed_dev_token_esp32_01_a1b2c3d4e5f6"

/* One run per boot — no loop. Re-flash or reboot to repeat. */
#define RUN_ID        "1"

/* Buffer sizes */
#define AUTH_BODY_BUF_SIZE    256
#define AUTH_REQ_BUF_SIZE     512
#define AUTH_RESP_BUF_SIZE    512   /* accumulate full auth response for JSON parse */
#define SESSION_TOKEN_SIZE     64   /* 32 hex chars + null */
#define CSR_BUF_SIZE         2048
#define CSR_JSON_BUF_SIZE    4096
#define ENROLL_BODY_BUF_SIZE 4608
#define ENROLL_REQ_BUF_SIZE  6144
#define RECV_CHUNK_SIZE       128

static const char *TAG = "example";

/* -----------------------------------------------------------------------
   Forward declarations
   ----------------------------------------------------------------------- */
static void json_escape_string(const char *src, char *dst, size_t dst_size);
static int  extract_json_string(const char *json, const char *key,
                                char *out, size_t out_size);
static int  generate_csr(char *csr_buf, size_t buf_len);
static int  send_all(int sock, const char *buf, size_t len);

/* -----------------------------------------------------------------------
   Unresolved timestamp variables — declared here so goto jumps over
   initialisers without compiler complaints.
   ----------------------------------------------------------------------- */
static int64_t t_auth_start_us   = 0;
static int64_t t_auth_end_us     = 0;
static int64_t t_csr_start_us    = 0;
static int64_t t_csr_end_us      = 0;
static int64_t t_enroll_start_us = 0;
static int64_t t_enroll_end_us   = 0;

/* -----------------------------------------------------------------------
   Open a TCP connection to WEB_SERVER:WEB_PORT.
   Returns socket fd >= 0 on success, -1 on failure.
   ----------------------------------------------------------------------- */
static int open_connection(void)
{
    const struct addrinfo hints = {
        .ai_family   = AF_INET,
        .ai_socktype = SOCK_STREAM,
    };

    struct addrinfo *res = NULL;
    int err = getaddrinfo(WEB_SERVER, WEB_PORT, &hints, &res);
    if (err != 0 || res == NULL) {
        ESP_LOGE(TAG, "DNS lookup failed err=%d", err);
        return -1;
    }

    struct in_addr *addr = &((struct sockaddr_in *)res->ai_addr)->sin_addr;
    ESP_LOGI(TAG, "DNS ok IP=%s", inet_ntoa(*addr));

    int s = socket(res->ai_family, res->ai_socktype, 0);
    if (s < 0) {
        ESP_LOGE(TAG, "socket alloc failed");
        freeaddrinfo(res);
        return -1;
    }

    if (connect(s, res->ai_addr, res->ai_addrlen) != 0) {
        ESP_LOGE(TAG, "connect failed errno=%d", errno);
        close(s);
        freeaddrinfo(res);
        return -1;
    }

    freeaddrinfo(res);
    return s;
}

/* -----------------------------------------------------------------------
   Receive full response into buf (up to buf_size-1 bytes).
   Parses HTTP status from first chunk.  Returns total bytes received.
   ----------------------------------------------------------------------- */
static int recv_response(int sock, char *buf, size_t buf_size,
                         int *http_status_out, int timeout_sec)
{
    struct timeval tv = {.tv_sec = timeout_sec, .tv_usec = 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    char chunk[RECV_CHUNK_SIZE];
    int  total = 0;
    int  r;
    *http_status_out = -1;

    do {
        bzero(chunk, sizeof(chunk));
        r = read(sock, chunk, sizeof(chunk) - 1);
        if (r > 0) {
            if (*http_status_out < 0) {
                int parsed = -1;
                if (sscanf(chunk, "HTTP/%*d.%*d %d", &parsed) == 1) {
                    *http_status_out = parsed;
                }
            }
            if (total + r < (int)buf_size - 1) {
                memcpy(buf + total, chunk, r);
                total += r;
            }
        }
    } while (r > 0);

    buf[total] = '\0';
    return total;
}

/* -----------------------------------------------------------------------
   Main task — one full proposed-method onboarding session per boot
   ----------------------------------------------------------------------- */
static void http_proposed_task(void *pvParameters)
{
    int   http_status_auth   = -1;
    int   http_status_enroll = -1;
    bool  cert_received      = false;

    uint32_t heap_before = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    int64_t  t_total_start_us = esp_timer_get_time();

    /* ---- Stack-allocated Phase 1 buffers (small) ---------------------- */
    char auth_body[AUTH_BODY_BUF_SIZE];
    char auth_req[AUTH_REQ_BUF_SIZE];
    char auth_resp[AUTH_RESP_BUF_SIZE];
    char session_token[SESSION_TOKEN_SIZE];

    /* ---- Heap buffers for Phase 2 -------------------------------------- */
    char *csr_buf     = calloc(1, CSR_BUF_SIZE);
    char *csr_json    = calloc(1, CSR_JSON_BUF_SIZE);
    char *enroll_body = calloc(1, ENROLL_BODY_BUF_SIZE);
    char *enroll_req  = calloc(1, ENROLL_REQ_BUF_SIZE);

    if (!csr_buf || !csr_json || !enroll_body || !enroll_req) {
        ESP_LOGE(TAG, "Heap allocation failed — aborting");
        goto cleanup;
    }

    /* ==================================================================
       PHASE 1 — Local Gateway Authentication
       ================================================================== */
    ESP_LOGI(TAG, "=== Phase 1: Auth ===");
    t_auth_start_us = esp_timer_get_time();

    int auth_body_len = snprintf(auth_body, sizeof(auth_body),
        "{\"device_id\":\"" DEVICE_ID "\","
         "\"device_token\":\"" DEVICE_TOKEN "\"}");
    if (auth_body_len < 0 || auth_body_len >= AUTH_BODY_BUF_SIZE) {
        ESP_LOGE(TAG, "Auth body overflow");
        t_auth_end_us = esp_timer_get_time();
        goto measure;
    }

    int auth_req_len = snprintf(auth_req, sizeof(auth_req),
        "POST " AUTH_PATH " HTTP/1.0\r\n"
        "Host: " WEB_SERVER ":" WEB_PORT "\r\n"
        "User-Agent: esp-idf/1.0 esp32\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "\r\n"
        "%s",
        auth_body_len, auth_body);
    if (auth_req_len < 0 || auth_req_len >= AUTH_REQ_BUF_SIZE) {
        ESP_LOGE(TAG, "Auth request overflow");
        t_auth_end_us = esp_timer_get_time();
        goto measure;
    }

    {
        int s1 = open_connection();
        if (s1 < 0) {
            ESP_LOGE(TAG, "Phase 1 connect failed");
            t_auth_end_us = esp_timer_get_time();
            goto measure;
        }
        ESP_LOGI(TAG, "Phase 1 connected");

        if (send_all(s1, auth_req, (size_t)auth_req_len) != 0) {
            ESP_LOGE(TAG, "Phase 1 send failed errno=%d", errno);
            close(s1);
            t_auth_end_us = esp_timer_get_time();
            goto measure;
        }
        ESP_LOGI(TAG, "Phase 1 sent");

        recv_response(s1, auth_resp, sizeof(auth_resp), &http_status_auth, 10);
        close(s1);
    }

    t_auth_end_us = esp_timer_get_time();
    ESP_LOGI(TAG, "Phase 1 http_status=%d latency=%" PRIu32 " ms",
             http_status_auth,
             (uint32_t)((t_auth_end_us - t_auth_start_us) / 1000));

    if (http_status_auth != 200) {
        ESP_LOGE(TAG, "Phase 1 FAILED — aborting");
        goto measure;
    }

    if (extract_json_string(auth_resp, "session_token",
                             session_token, sizeof(session_token)) <= 0) {
        ESP_LOGE(TAG, "Failed to parse session_token");
        goto measure;
    }
    ESP_LOGI(TAG, "Phase 1 OK — session_token=%.8s...", session_token);

    /* ==================================================================
       CSR GENERATION
       ================================================================== */
    ESP_LOGI(TAG, "=== Generating CSR ===");
    t_csr_start_us = esp_timer_get_time();

    if (generate_csr(csr_buf, CSR_BUF_SIZE) != 0) {
        ESP_LOGE(TAG, "CSR generation failed");
        t_csr_end_us = esp_timer_get_time();
        goto measure;
    }

    t_csr_end_us = esp_timer_get_time();
    ESP_LOGI(TAG, "CSR generated (%" PRIu32 " ms)",
             (uint32_t)((t_csr_end_us - t_csr_start_us) / 1000));

    json_escape_string(csr_buf, csr_json, CSR_JSON_BUF_SIZE);

    /* ==================================================================
       PHASE 2 — Gateway-Brokered Certificate Enrollment
       ================================================================== */
    ESP_LOGI(TAG, "=== Phase 2: Enroll ===");
    t_enroll_start_us = esp_timer_get_time();

    int enroll_body_len = snprintf(enroll_body, ENROLL_BODY_BUF_SIZE,
        "{\"run_id\":\"" RUN_ID "\","
         "\"device_id\":\"" DEVICE_ID "\","
         "\"session_token\":\"%s\","
         "\"csr_pem\":\"%s\"}",
        session_token, csr_json);
    if (enroll_body_len < 0 || enroll_body_len >= ENROLL_BODY_BUF_SIZE) {
        ESP_LOGE(TAG, "Enroll body overflow");
        t_enroll_end_us = esp_timer_get_time();
        goto measure;
    }

    int enroll_req_len = snprintf(enroll_req, ENROLL_REQ_BUF_SIZE,
        "POST " ENROLL_PATH " HTTP/1.0\r\n"
        "Host: " WEB_SERVER ":" WEB_PORT "\r\n"
        "User-Agent: esp-idf/1.0 esp32\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "\r\n"
        "%s",
        enroll_body_len, enroll_body);
    if (enroll_req_len < 0 || enroll_req_len >= ENROLL_REQ_BUF_SIZE) {
        ESP_LOGE(TAG, "Enroll request overflow");
        t_enroll_end_us = esp_timer_get_time();
        goto measure;
    }

    {
        /* Reuse enroll_body as Phase 2 response buffer — request is built,
           not needed any more.  Cert response fits in 4608 bytes. */
        char  *enroll_resp      = enroll_body;
        size_t enroll_resp_size = (size_t)ENROLL_BODY_BUF_SIZE;

        int s2 = open_connection();
        if (s2 < 0) {
            ESP_LOGE(TAG, "Phase 2 connect failed");
            t_enroll_end_us = esp_timer_get_time();
            goto measure;
        }
        ESP_LOGI(TAG, "Phase 2 connected");

        if (send_all(s2, enroll_req, (size_t)enroll_req_len) != 0) {
            ESP_LOGE(TAG, "Phase 2 send failed errno=%d", errno);
            close(s2);
            t_enroll_end_us = esp_timer_get_time();
            goto measure;
        }
        ESP_LOGI(TAG, "Phase 2 sent");

        recv_response(s2, enroll_resp, enroll_resp_size, &http_status_enroll, 30);
        close(s2);

        cert_received = (strstr(enroll_resp, "device_cert_pem") != NULL &&
                         strstr(enroll_resp, "ca_cert_pem")     != NULL);
    }

    t_enroll_end_us = esp_timer_get_time();

    ESP_LOGI(TAG, "Phase 2 http_status=%d cert_received=%d latency=%" PRIu32 " ms",
             http_status_enroll, (int)cert_received,
             (uint32_t)((t_enroll_end_us - t_enroll_start_us) / 1000));

    if (http_status_enroll == 200 && cert_received) {
        ESP_LOGI(TAG, "Phase 2 OK — device_cert_pem + ca_cert_pem received (RAM)");
    } else {
        ESP_LOGE(TAG, "Phase 2 FAILED");
    }

measure:;
    int64_t  t_total_end_us   = esp_timer_get_time();
    uint32_t heap_after       = heap_caps_get_free_size(MALLOC_CAP_8BIT);
    int32_t  heap_delta       = (int32_t)heap_after - (int32_t)heap_before;
    uint32_t total_latency_ms = (uint32_t)((t_total_end_us - t_total_start_us) / 1000);

    uint32_t auth_lat   = (uint32_t)((t_auth_end_us   - t_auth_start_us)   / 1000);
    uint32_t csr_lat    = (uint32_t)((t_csr_end_us    - t_csr_start_us)    / 1000);
    uint32_t enroll_lat = (uint32_t)((t_enroll_end_us - t_enroll_start_us) / 1000);

    bool pass = (http_status_auth   == 200 &&
                 http_status_enroll == 200 &&
                 cert_received);

    printf("PROPOSED_MEASURE"
           " run_id=" RUN_ID
           " auth_latency_ms=%" PRIu32
           " csr_gen_ms=%" PRIu32
           " enroll_latency_ms=%" PRIu32
           " total_latency_ms=%" PRIu32
           " heap_before=%" PRIu32
           " heap_after=%" PRIu32
           " heap_delta=%ld"
           " http_status_auth=%d"
           " http_status_enroll=%d"
           " cert_received=%d"
           " result=%s\n",
           auth_lat, csr_lat, enroll_lat, total_latency_ms,
           heap_before, heap_after, (long)heap_delta,
           http_status_auth, http_status_enroll, (int)cert_received,
           pass ? "PASS" : "FAIL");

    ESP_LOGI(TAG, "PROPOSED session complete result=%s", pass ? "PASS" : "FAIL");

cleanup:
    free(csr_buf);
    free(csr_json);
    free(enroll_body);
    free(enroll_req);
    vTaskDelete(NULL);
}

/* -----------------------------------------------------------------------
   JSON string escaping — same as baseline3
   ----------------------------------------------------------------------- */
static void json_escape_string(const char *src, char *dst, size_t dst_size)
{
    size_t j = 0;
    for (size_t i = 0; src[i] != '\0' && j < dst_size - 2; i++) {
        if (src[i] == '\n') {
            dst[j++] = '\\'; dst[j++] = 'n';
        } else if (src[i] == '\"') {
            dst[j++] = '\\'; dst[j++] = '\"';
        } else if (src[i] == '\\') {
            dst[j++] = '\\'; dst[j++] = '\\';
        } else {
            dst[j++] = src[i];
        }
    }
    dst[j] = '\0';
}

/* -----------------------------------------------------------------------
   Extract a JSON string value — finds "key":"value" and copies value.
   Returns extracted length, or -1 if not found.
   ----------------------------------------------------------------------- */
static int extract_json_string(const char *json, const char *key,
                                char *out, size_t out_size)
{
    /* Find "key" anywhere in the buffer */
    char search[80];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *p = strstr(json, search);
    if (!p) return -1;
    p += strlen(search);

    /* Skip optional whitespace, then expect ':', then optional whitespace,
       then opening '"'.  Handles both compact {"k":"v"} and spaced {"k": "v"}
       JSON as produced by Python's default json.dumps separator style. */
    while (*p == ' ' || *p == '\t') p++;
    if (*p != ':') return -1;
    p++;
    while (*p == ' ' || *p == '\t') p++;
    if (*p != '"') return -1;
    p++;  /* skip opening quote */

    size_t i = 0;
    while (*p && *p != '"' && i < out_size - 1) {
        out[i++] = *p++;
    }
    out[i] = '\0';
    return (int)i;
}

/* -----------------------------------------------------------------------
   EC keypair + CSR generation — identical to baseline3
   ----------------------------------------------------------------------- */
static int generate_keypair(mbedtls_pk_context *key,
                             mbedtls_ctr_drbg_context *ctr_drbg)
{
    int ret;
    mbedtls_pk_init(key);
    ret = mbedtls_pk_setup(key, mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
    if (ret != 0) return ret;

    ret = mbedtls_ecp_gen_key(MBEDTLS_ECP_DP_SECP256R1, mbedtls_pk_ec(*key),
                               mbedtls_ctr_drbg_random, ctr_drbg);
    if (ret != 0) mbedtls_pk_free(key);
    return ret;
}

static int generate_csr(char *csr_buf, size_t buf_len)
{
    int ret;
    mbedtls_pk_context      key;
    mbedtls_x509write_csr   req;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
    const char *pers = "csr";

    mbedtls_pk_init(&key);
    mbedtls_x509write_csr_init(&req);
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);

    ret = mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy,
                                 (const unsigned char *)pers, strlen(pers));
    if (ret != 0) goto cleanup;

    ret = generate_keypair(&key, &ctr_drbg);
    if (ret != 0) goto cleanup;

    mbedtls_x509write_csr_set_key(&req, &key);
    mbedtls_x509write_csr_set_md_alg(&req, MBEDTLS_MD_SHA256);

    ret = mbedtls_x509write_csr_set_subject_name(&req, "CN=" DEVICE_ID);
    if (ret != 0) goto cleanup;

    ret = mbedtls_x509write_csr_pem(&req, (unsigned char *)csr_buf, buf_len,
                                     mbedtls_ctr_drbg_random, &ctr_drbg);
cleanup:
    mbedtls_x509write_csr_free(&req);
    mbedtls_pk_free(&key);
    mbedtls_ctr_drbg_free(&ctr_drbg);
    mbedtls_entropy_free(&entropy);
    return ret;
}

/* -----------------------------------------------------------------------
   Reliable socket write
   ----------------------------------------------------------------------- */
static int send_all(int sock, const char *buf, size_t len)
{
    size_t sent = 0;
    while (sent < len) {
        int w = write(sock, buf + sent, len - sent);
        if (w < 0) return -1;
        sent += (size_t)w;
    }
    return 0;
}

/* -----------------------------------------------------------------------
   app_main
   ----------------------------------------------------------------------- */
void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(example_connect());

    xTaskCreate(&http_proposed_task, "http_proposed_task", 8192, NULL, 5, NULL);
}
