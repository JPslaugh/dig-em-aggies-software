// Safety
#ifndef SAFETY_HPP
#define SAFETY_HPP

#include "base.hpp"
#include "sensors.hpp"
#include "actuators.hpp"
#include <vector>
#include <memory>
#include <functional>

struct SafetyLimit {
    std::string name;
    std::function<double()> getValue;
    double minValue;
    double maxValue;
    bool isActive;
};

class SafetyMonitor : public ISystemComponent {
private:
    std::vector<SafetyLimit> limits_;
    std::vector<std::shared_ptr<IActuator>> controlledActuators_;
    bool systemSafe_;
    std::string lastViolation_;

public:
    SafetyMonitor() : systemSafe_(true) {}

    bool initialize() override {
        systemSafe_ = true;
        return true;
    }

    bool update() override {
        systemSafe_ = true;
        
        for (auto& limit : limits_) {
            double value = limit.getValue();
            
            if (value < limit.minValue || value > limit.maxValue) {
                systemSafe_ = false;
                lastViolation_ = limit.name + " out of range: " + 
                                std::to_string(value);
                limit.isActive = true;
                
                // Trigger interlocks
                for (auto& actuator : controlledActuators_) {
                    actuator->setCommand(0.0);
                }
                break;
            } else {
                limit.isActive = false;
            }
        }
        
        return true;
    }

    bool shutdown() override {
        // Safe shutdown of all actuators
        for (auto& actuator : controlledActuators_) {
            actuator->shutdown();
        }
        return true;
    }

    void addLimit(const std::string& name, 
                  std::function<double()> getValue,
                  double minVal, double maxVal) {
        limits_.push_back({name, getValue, minVal, maxVal, false});
    }

    void addActuator(std::shared_ptr<IActuator> actuator) {
        controlledActuators_.push_back(actuator);
    }

    bool isSystemSafe() const { return systemSafe_; }
    std::string getLastViolation() const { return lastViolation_; }

    std::string getStatus() const override {
        return systemSafe_ ? "System Safe" : "FAULT: " + lastViolation_;
    }

    std::string getComponentName() const override { return "SafetyMonitor"; }
};

#endif