// Calls original converters; owns only job decoding and fresh-process state reset.
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <spawn.h>
#include <stdexcept>
#include <string>
#include <sys/wait.h>
#include <vector>
#include <cerrno>
extern "C" int hg_nitrogfx_main(int, char **);
int hg_jsonproc_main(int, char **);
extern std::map<std::string, std::string> customVars;
extern char **environ;
static uint32_t number(std::istream &in) {
    unsigned char b[4];
    if (!in.read(reinterpret_cast<char *>(b), 4)) throw std::runtime_error("truncated job");
    return uint32_t(b[0]) | uint32_t(b[1]) << 8 | uint32_t(b[2]) << 16 | uint32_t(b[3]) << 24;
}
int main(int argc, char **argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: asset_worker jobs.bin");
        std::ifstream in(argv[1], std::ios::binary);
        if (number(in) != 0x31424748) throw std::runtime_error("invalid job format");
        auto count = number(in);
        if (count > 100000) throw std::runtime_error("too many jobs");
        // Validate the whole manifest before executing any converter.
        struct Job { uint32_t kind; std::vector<std::string> args; };
        std::vector<Job> jobs;
        for (uint32_t j = 0; j < count; ++j) {
            Job job{number(in), {}};
            auto n = number(in);
            if (job.kind > 3 || n == 0 || n > 256) throw std::runtime_error("invalid job");
            for (uint32_t a = 0; a < n; ++a) {
                auto size = number(in);
                if (size > 1048576) throw std::runtime_error("oversized argument");
                std::string arg(size, '\0');
                if (!in.read(arg.data(), size) || arg.find('\0') != std::string::npos)
                    throw std::runtime_error("invalid argument");
                job.args.push_back(std::move(arg));
            }
            if (job.kind == 0 && n != 2) throw std::runtime_error("invalid copy");
            jobs.push_back(std::move(job));
        }
        if (in.peek() != EOF) throw std::runtime_error("trailing job data");
        for (auto &job : jobs) {
            if (job.kind == 0) {
                std::filesystem::copy_file(job.args[0], job.args[1]);
                continue;
            }
            std::vector<char *> args;
            for (auto &arg : job.args) args.push_back(arg.data());
            args.push_back(nullptr);
            int status = 0;
            if (job.kind == 1) status = hg_nitrogfx_main(int(args.size()) - 1, args.data());
            else if (job.kind == 2) {
                customVars.clear(); // Original CLI has a fresh map for every process.
                status = hg_jsonproc_main(int(args.size()) - 1, args.data());
            } else {
                pid_t pid;
                if (posix_spawn(&pid, args[0], nullptr, nullptr, args.data(), environ))
                    throw std::runtime_error("spawn failed: " + job.args[0]);
                int result;
                while (waitpid(pid, &result, 0) < 0)
                    if (errno != EINTR) throw std::runtime_error("wait failed");
                status = WIFEXITED(result) ? WEXITSTATUS(result) : 128 + WTERMSIG(result);
            }
            if (status) return status;
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "asset batch: " << error.what() << '\n';
        return 1;
    }
}
