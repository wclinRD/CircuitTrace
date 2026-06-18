module soc_top (
    input wire clk,
    input wire rst_n,
    input wire rx,
    output wire tx,
    output wire [7:0] gpio
);

    wire [31:0] cpu_inst;
    wire [31:0] cpu_pc;
    wire [31:0] mem_rdata;
    wire [31:0] mem_wdata;
    wire [31:0] mem_addr;
    wire mem_we;
    wire mem_en;

    wire [31:0] apb_paddr;
    wire apb_psel;
    wire apb_penable;
    wire apb_pwrite;
    wire [31:0] apb_pwdata;
    wire [31:0] apb_prdata;
    wire apb_pready;

    cpu_core u_cpu (
        .clk(clk),
        .rst_n(rst_n),
        .inst(cpu_inst),
        .mem_rdata(mem_rdata),
        .pc(cpu_pc),
        .mem_wdata(mem_wdata),
        .mem_addr(mem_addr),
        .mem_we(mem_we),
        .mem_en(mem_en)
    );

    memory_ctrl u_mem_ctrl (
        .clk(clk),
        .rst_n(rst_n),
        .en(mem_en),
        .we(mem_we),
        .addr(mem_addr),
        .wdata(mem_wdata),
        .rdata(mem_rdata),
        .inst_out(cpu_inst)
    );

    apb_bus u_apb_bus (
        .clk(clk),
        .rst_n(rst_n),
        .cpu_addr(mem_addr),
        .cpu_wdata(mem_wdata),
        .cpu_we(mem_we),
        .cpu_en(mem_en),
        .apb_paddr(apb_paddr),
        .apb_psel(apb_psel),
        .apb_penable(apb_penable),
        .apb_pwrite(apb_pwrite),
        .apb_pwdata(apb_pwdata),
        .apb_prdata(apb_prdata),
        .apb_pready(apb_pready)
    );

    uart_top u_uart (
        .pclk(clk),
        .presetn(rst_n),
        .paddr(apb_paddr),
        .psel(apb_psel),
        .penable(apb_penable),
        .pwrite(apb_pwrite),
        .pwdata(apb_pwdata),
        .prdata(apb_prdata),
        .pready(apb_pready),
        .rx(rx),
        .tx(tx)
    );

    timer u_timer (
        .clk(clk),
        .rst_n(rst_n),
        .en(1'b1),
        .timeout()
    );

endmodule
