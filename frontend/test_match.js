const allFullNames = [
  "tb.gpio[7:0]",
  "tb.tx",
  "tb.clk",
  "tb.u_soc.mem_addr[31:0]"
];
const shortName = "mem_addr";
const matches = allFullNames.filter(fn => {
  const fnBase = fn.replace(/\[.*\]$/, '');
  return fnBase.endsWith('.' + shortName) || fnBase === shortName;
});
console.log(matches);
