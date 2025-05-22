#include "board.h"
#include "peripherals.h"
#include "pin_mux.h"
#include "clock_config.h"
#include "MKL46Z4.h"
#include "fsl_debug_console.h"

#define SW1_PIN 3
#define SW1_PORT PORTC

void InitSW1(void) {
    //clock to portc
    SIM->SCGC5 |= SIM_SCGC5_PORTC_MASK;
    // PTC3 as GPIO input with pull-up
    PORTC->PCR[SW1_PIN] = PORT_PCR_MUX(1) | PORT_PCR_PE_MASK | PORT_PCR_PS_MASK;

    PTC->PDDR &= ~(1 << SW1_PIN);
    PORTC->PCR[SW1_PIN] |= PORT_PCR_IRQC(10);

    //PORTC and PORTD share an interrupt vector
    NVIC_EnableIRQ(PORTC_PORTD_IRQn);
}

// PORTC_PORTD interrupt handler (shared for both ports)
void PORTC_PORTD_IRQHandler(void) {
    // Check if interrupt was from SW1 (PTC3)
    if (PORTC->PCR[SW1_PIN] & PORT_PCR_ISF_MASK) {
        // Clear interrupt flag
        PORTC->PCR[SW1_PIN] |= PORT_PCR_ISF_MASK;

        PRINTF("JUMP\n");
    }
}

int main(void) {
    BOARD_InitBootPins();
    BOARD_InitBootClocks();
    BOARD_InitBootPeripherals();

    BOARD_InitDebugConsole();
    InitSW1();

    PRINTF("FRDM-KL46Z Flappy Bird Controller Ready\n");

    while(1) {
        __WFI(); 
    }

    return 0;
}
