// ECUManager
#ifndef ECU_MANAGER_HPP
#define ECU_MANAGER_HPP

#include "ecu.hpp"
#include "data_logger.hpp"
#include <map>
#include <algorithm>
#include <fstream>
#include <iostream>

class ECUManager : public ISystemComponent {
private:
    std::map<std::string, std::shared_ptr<ECU>> ecus_;
    std::shared_ptr<DataLogger> logger_;
    bool allECUsOnline_;
    std::string systemName_;

public:
    ECUManager(const std::string& systemName, std::shared_ptr<DataLogger> logger)
        : systemName_(systemName), logger_(logger), allECUsOnline_(false) {}

    bool initialize() override {
        if (logger_) {
            logger_->log("ECU Manager initializing...");
        }

        bool success = true;
        for (auto& [id, ecu] : ecus_) {
            if (!ecu->initialize()) {
                if (logger_) {
                    logger_->log("Failed to initialize ECU: " + id);
                }
                success = false;
            } else {
                if (logger_) {
                    logger_->log("ECU initialized: " + id);
                }
            }
        }

        updateSystemStatus();
        return success;
    }

    bool update() override {
        bool allOK = true;
        
        for (auto& [id, ecu] : ecus_) {
            if (!ecu->update()) {
                allOK = false;
            }
        }

        updateSystemStatus();
        return allOK;
    }

    bool shutdown() override {
        if (logger_) {
            logger_->log("Shutting down all ECUs...");
        }

        for (auto& [id, ecu] : ecus_) {
            ecu->shutdown();
        }

        allECUsOnline_ = false;
        return true;
    }

    std::string getStatus() const override {
        int online = 0, offline = 0, fault = 0, degraded = 0;

        for (const auto& [id, ecu] : ecus_) {
            switch (ecu->getECUStatus()) {
                case ECUStatus::ONLINE: online++; break;
                case ECUStatus::OFFLINE: offline++; break;
                case ECUStatus::FAULT: fault++; break;
                case ECUStatus::DEGRADED: degraded++; break;
                default: break;
            }
        }

        std::stringstream ss;
        ss << "ECUs: " << online << " online, " << degraded << " degraded, "
           << fault << " fault, " << offline << " offline";
        return ss.str();
    }

    std::string getComponentName() const override {
        return "ECUManager";
    }

    // Add ECU to system
    void addECU(std::shared_ptr<ECU> ecu) {
        ecus_[ecu->getECUID()] = ecu;
        if (logger_) {
            logger_->log("Added ECU: " + ecu->getECUID() + " - " + 
                        ecu->getComponentName());
        }
    }

    // Get specific ECU
    std::shared_ptr<ECU> getECU(const std::string& ecuID) {
        auto it = ecus_.find(ecuID);
        if (it != ecus_.end()) {
            return it->second;
        }
        return nullptr;
    }

    // Get all ECUs of a specific type
    std::vector<std::shared_ptr<ECU>> getECUsByType(ECUType type) {
        std::vector<std::shared_ptr<ECU>> result;
        
        for (const auto& [id, ecu] : ecus_) {
            if (ecu->getType() == type) {
                result.push_back(ecu);
            }
        }
        
        return result;
    }

    // System health check
    bool areAllECUsOnline() const {
        return allECUsOnline_;
    }

    int getTotalECUCount() const {
        return ecus_.size();
    }

    int getOnlineECUCount() const {
        int count = 0;
        for (const auto& [id, ecu] : ecus_) {
            if (ecu->getECUStatus() == ECUStatus::ONLINE) {
                count++;
            }
        }
        return count;
    }

    // Generate ECU table for documentation
    std::string generateECUTable() const {
        std::stringstream ss;
        
        ss << "\n";
        ss << "╔══════════════════════════════════════════════════════════════════════════════════════════════╗\n";
        ss << "║                                   " << systemName_ << " - ECU TABLE                                   ║\n";
        ss << "╠════════╦══════════════════════════╦═══════════════════╦══════════════════════════════════════╣\n";
        ss << "║ ECU ID ║ Name                     ║ Type              ║ Location                             ║\n";
        ss << "╠════════╬══════════════════════════╬═══════════════════╬══════════════════════════════════════╣\n";

        for (const auto& [id, ecu] : ecus_) {
            ss << "║ " << std::left << std::setw(6) << id << " ║ ";
            ss << std::setw(24) << ecu->getComponentName() << " ║ ";
            
            std::string typeStr;
            switch (ecu->getType()) {
                case ECUType::MAIN_CONTROLLER: typeStr = "Main Controller"; break;
                case ECUType::SENSOR_NODE: typeStr = "Sensor Node"; break;
                case ECUType::ACTUATOR_NODE: typeStr = "Actuator Node"; break;
                case ECUType::VFD_CONTROLLER: typeStr = "VFD"; break;
                case ECUType::HYDRAULIC_CONTROLLER: typeStr = "Hydraulic Ctrl"; break;
                default: typeStr = "Custom"; break;
            }
            ss << std::setw(17) << typeStr << " ║ ";
            ss << std::setw(36) << ecu->getLocation().compartment << " ║\n";

            // List controlled devices
            const auto& devices = ecu->getControlledDevices();
            if (!devices.empty()) {
                ss << "║        ║ Controls:                                                                       ║\n";
                for (const auto& device : devices) {
                    ss << "║        ║   • " << std::setw(72) << std::left 
                       << (device.deviceName + " (" + device.deviceType + ")") << " ║\n";
                }
            }
            
            ss << "╠════════╬══════════════════════════╬═══════════════════╬══════════════════════════════════════╣\n";
        }

        ss << "║ TOTAL  ║ " << std::setw(24) << (std::to_string(ecus_.size()) + " ECUs") 
           << " ║                   ║                                      ║\n";
        ss << "╚════════╩══════════════════════════╩═══════════════════╩══════════════════════════════════════╝\n";

        return ss.str();
    }

    // Generate detailed reports for all ECUs
    void generateDetailedReports(const std::string& outputDirectory = "./ecu_reports/") {
        // Create directory if needed (platform-specific, placeholder)
        
        // Generate individual ECU reports
        for (const auto& [id, ecu] : ecus_) {
            std::string filename = outputDirectory + "ECU_" + id + "_report.txt";
            std::ofstream file(filename);
            
            if (file.is_open()) {
                file << ecu->generateReport();
                file.close();
                
                if (logger_) {
                    logger_->log("Generated report for ECU " + id + ": " + filename);
                }
            }
        }

        // Generate summary table
        std::string summaryFile = outputDirectory + "ECU_Summary.txt";
        std::ofstream file(summaryFile);
        if (file.is_open()) {
            file << generateECUTable();
            file << "\n\nSystem Status: " << getStatus() << "\n";
            file << "Generated: " << getCurrentTimestamp() << "\n";
            file.close();
        }
    }

    // Print status to console
    void printSystemStatus() const {
        std::cout << generateECUTable() << std::endl;
        std::cout << "\nSystem Status: " << getStatus() << std::endl;
    }

private:
    void updateSystemStatus() {
        allECUsOnline_ = true;
        
        for (const auto& [id, ecu] : ecus_) {
            if (ecu->getECUStatus() != ECUStatus::ONLINE) {
                allECUsOnline_ = false;
                break;
            }
        }
    }

    std::string getCurrentTimestamp() const {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
        return ss.str();
    }
};

#endif // ECU_MANAGER_HPP