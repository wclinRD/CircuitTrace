module apb_bus (
    input wire clk,
    input wire rst_n,
    input wire [31:0] cpu_addr,
    input wire [31:0] cpu_wdata,
    input wire cpu_we,
    input wire cpu_en,
    
    output wire [31:0] apb_paddr,
    output wire apb_psel,
    output wire apb_penable,
    output wire apb_pwrite,
    output wire [31:0] apb_pwdata,
    input wire [31:0] apb_prdata,
    input wire apb_pready
);
    reg state;
    localparam IDLE = 1'b0;
    localparam SETUP = 1'b1;

    assign apb_paddr = cpu_addr;
    assign apb_pwdata = cpu_wdata;
    assign apb_pwrite = cpu_we;
    assign apb_psel = cpu_en && (cpu_addr[31:28] == 4'h4);
    assign apb_penable = (state == SETUP);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            case (state)
                IDLE: if (apb_psel) state <= SETUP;
                SETUP: if (apb_pready) state <= IDLE;
            endcase
        end
    end
endmodule
