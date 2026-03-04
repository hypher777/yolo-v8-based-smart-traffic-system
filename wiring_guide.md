# Hardware Wiring Guide (Road 1 Module)

You have the **4-pin Traffic Light Modules** (Electrobot). These are great because the resistors are already built-in!

## 1. Module Pinout (Road 1)
Connect the pins on the module directly to the Arduino:

| Module Pin | Arduino Pin | Description |
| :--- | :--- | :--- |
| **GND** | **GND** | Ground (Negative) |
| **R** | **Pin 8** | Red Signal |
| **Y** | **Pin 9** | Yellow Signal |
| **G** | **Pin 10** | Green Signal |

## 2. Full 4-Way Traffic Setup
Repeat the same logic for your other modules using these pins defined in the code:

### Road 2 Module
*   **GND** -> GND
*   **R** -> Pin 2
*   **Y** -> Pin 3
*   **G** -> Pin 4

### Road 3 Module
*   **GND** -> GND
*   **R** -> Pin 5
*   **Y** -> Pin 6
*   **G** -> Pin 7

### Road 4 Module
*   **GND** -> GND
*   **R** -> Pin 11
*   **Y** -> Pin 12
*   **G** -> Pin 13

> [!IMPORTANT]
> Since you have multiple modules, make sure you connect the **GND** of every module to a GND pin on the Arduino (you can use a breadboard to share one GND pin if needed).
