`timescale 1ns/1ps

module tb;

    reg clk;
    reg rst_n;
    reg rx;
    wire tx;
    wire [7:0] gpio;

    soc_top u_soc (
        .clk(clk),
        .rst_n(rst_n),
        .rx(rx),
        .tx(tx),
        .gpio(gpio)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // Stimulus and waveform generation
    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, tb);

        // Initialize inputs
        rst_n = 0;
        rx = 1;

        #20;
        rst_n = 1; // Release reset

        #50;
        rx = 0; // Simulate some UART rx activity
        #10;
        rx = 1;

        #200;
        $display("Simulation completed successfully.");
        $finish;
    end

endmodule
