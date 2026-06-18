import os

base_dir = "/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project"

files = {
    "soc_top.v": """
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
""",
    "cpu_core.v": """
module cpu_core (
    input wire clk,
    input wire rst_n,
    input wire [31:0] inst,
    input wire [31:0] mem_rdata,
    output wire [31:0] pc,
    output wire [31:0] mem_wdata,
    output wire [31:0] mem_addr,
    output wire mem_we,
    output wire mem_en
);
    wire [31:0] fetch_pc;
    wire [31:0] dec_imm;
    wire [4:0] dec_rs1;
    wire [4:0] dec_rs2;
    wire [4:0] dec_rd;
    wire [3:0] dec_alu_op;
    
    wire [31:0] alu_result;
    wire branch_taken;

    assign pc = fetch_pc;
    assign mem_addr = alu_result;
    assign mem_wdata = 32'h0;
    assign mem_we = 1'b0;
    assign mem_en = 1'b1;

    fetch_unit u_fetch (
        .clk(clk),
        .rst_n(rst_n),
        .branch_taken(branch_taken),
        .branch_target(alu_result),
        .pc(fetch_pc)
    );

    decode_unit u_decode (
        .inst(inst),
        .imm(dec_imm),
        .rs1(dec_rs1),
        .rs2(dec_rs2),
        .rd(dec_rd),
        .alu_op(dec_alu_op)
    );

    execute_unit u_execute (
        .rs1_data(fetch_pc),
        .rs2_data(dec_imm),
        .alu_op(dec_alu_op),
        .alu_result(alu_result),
        .branch_taken(branch_taken)
    );

endmodule
""",
    "fetch.v": """
module fetch_unit (
    input wire clk,
    input wire rst_n,
    input wire branch_taken,
    input wire [31:0] branch_target,
    output reg [31:0] pc
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 32'h0000_0000;
        end else if (branch_taken) begin
            pc <= branch_target;
        end else begin
            pc <= pc + 4;
        end
    end
endmodule
""",
    "decode_unit.v": """
module decode_unit (
    input wire [31:0] inst,
    output wire [31:0] imm,
    output wire [4:0] rs1,
    output wire [4:0] rs2,
    output wire [4:0] rd,
    output wire [3:0] alu_op
);
    assign rd = inst[11:7];
    assign rs1 = inst[19:15];
    assign rs2 = inst[24:20];
    assign imm = { {20{inst[31]}}, inst[31:20] };
    
    assign alu_op = inst[6:3];
endmodule
""",
    "execute.v": """
module execute_unit (
    input wire [31:0] rs1_data,
    input wire [31:0] rs2_data,
    input wire [3:0] alu_op,
    output reg [31:0] alu_result,
    output reg branch_taken
);
    always @(*) begin
        case (alu_op)
            4'b0000: alu_result = rs1_data + rs2_data;
            4'b0001: alu_result = rs1_data - rs2_data;
            4'b0010: alu_result = rs1_data & rs2_data;
            4'b0011: alu_result = rs1_data | rs2_data;
            4'b0100: alu_result = rs1_data ^ rs2_data;
            default: alu_result = 32'h0;
        endcase
        
        branch_taken = (alu_op == 4'b1000) && (rs1_data == rs2_data);
    end
endmodule
""",
    "memory_ctrl.v": """
module memory_ctrl (
    input wire clk,
    input wire rst_n,
    input wire en,
    input wire we,
    input wire [31:0] addr,
    input wire [31:0] wdata,
    output reg [31:0] rdata,
    output reg [31:0] inst_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rdata <= 32'h0;
            inst_out <= 32'h0000_0013;
        end else if (en) begin
            if (we) begin
            end else begin
                rdata <= 32'hDEADBEEF;
                inst_out <= 32'h0000_0013;
            end
        end
    end
endmodule
""",
    "apb_bus.v": """
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
""",
    "uart.v": """
module uart_top (
    input wire pclk,
    input wire presetn,
    input wire [31:0] paddr,
    input wire psel,
    input wire penable,
    input wire pwrite,
    input wire [31:0] pwdata,
    output wire [31:0] prdata,
    output wire pready,
    
    input wire rx,
    output wire tx
);
    assign pready = 1'b1;
    assign prdata = 32'h0;
    assign tx = rx;
endmodule
""",
    "timer.v": """
module timer (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg timeout
);
    reg [31:0] count;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
            timeout <= 0;
        end else if (en) begin
            if (count == 32'hFFFF) begin
                count <= 0;
                timeout <= 1;
            end else begin
                count <= count + 1;
                timeout <= 0;
            end
        end
    end
endmodule
"""
}

project_f = ""
project_files = list(files.keys())
for filename, content in files.items():
    with open(os.path.join(base_dir, filename), "w") as f:
        f.write(content.strip() + "\n")

project_files.append("tb.v")
with open(os.path.join(base_dir, "project.f"), "w") as f:
    f.write("\n".join(project_files) + "\n")

print("Files generated properly.")
