from waveform import WaveformParser
parser = WaveformParser.get_instance()
parser.load_vcd('/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project/dump.vcd')
import json
print(json.dumps(parser.get_hierarchy(), indent=2))
