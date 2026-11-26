import re

with open('frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Radar View button from Overview toolbar
pattern = re.compile(
    r'\s*<button\s+onClick=\{\(\) => setShowRadarView\(\(prev\) => !prev\)\}.*?<\/button>',
    re.DOTALL
)
content, count = pattern.subn('', content, count=1)
print(f"Removed Radar View button: {count} occurrence(s)")

# 2. Update table conditional (remove showRadarView)
content = content.replace(
    '{(isCandidatesLoading && candidateList.length === 0) || showRadarView ? (',
    '{isCandidatesLoading && candidateList.length === 0 ? ('
)

# 3. Update sidebar button onClick
content = re.sub(
    r'onClick=\{\(\) => \{\s*setActiveNav\(item\.id\);\s*\}\}',
    'onClick={() => {\n                    navigateTo(item.id);\n                  }}',
    content
)

# 4. Update CandidateProfileView props
old_cand_props = '''          {activeNav === "candidate_profile" && selectedCandidate && (
            <CandidateProfileView
              candidate={selectedCandidate}
              candidateList={candidateList}
              onSelectCandidate={(cand) => setSelectedCandidate(cand)}
              onBack={() => {
                setSelectedCandidate(null);
                setActiveNav(previousNav || "overview");
              }}'''

new_cand_props = '''          {activeNav === "candidate_profile" && selectedCandidate && (
            <CandidateProfileView
              candidate={selectedCandidate}
              candidateList={candidateList}
              onSelectCandidate={(cand) => navigateTo("candidate_profile", cand)}
              onBack={() => {
                if (typeof window !== "undefined" && window.history.length > 1) {
                  window.history.back();
                } else {
                  navigateTo(previousNav || "overview");
                }
              }}'''

if old_cand_props in content:
    content = content.replace(old_cand_props, new_cand_props)
else:
    content = content.replace(old_cand_props.replace('\n', '\r\n'), new_cand_props.replace('\n', '\r\n'))

with open('frontend/src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 1 finished successfully!")

