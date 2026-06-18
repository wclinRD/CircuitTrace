from waveform import WaveformParser
parser = WaveformParser.get_instance()
parser.load_vcd('/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project/dump.vcd')
res = parser.get_signal_data("tb.clk", 0, 1000)
print(res)
