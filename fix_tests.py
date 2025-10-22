import re

# Read the test file
with open('tests/test_collectors.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all FabricAPIClient patch paths to use base module
content = re.sub(
    r"@patch\('fabricla_connector\.collectors\.(pipeline|dataset|capacity|user_activity)\.FabricAPIClient'\)",
    "@patch('fabricla_connector.collectors.base.FabricAPIClient')",
    content
)

# Write back
with open('tests/test_collectors.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all FabricAPIClient patch paths in test_collectors.py")
