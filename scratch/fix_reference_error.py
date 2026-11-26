with open('frontend/src/app/page.js', 'r', encoding='utf-8') as f:
    content = f.read()

# The navigation block currently at line 472 (before candidateList)
nav_block_start = '  // Route URL hash maps for browser back / forward history support'
nav_block_end = '    navigateTo,\n  ]);'
nav_block_end_crlf = '    navigateTo,\r\n  ]);'

assert nav_block_start in content, 'nav_block_start not found'

is_crlf = '\r\n' in content
end_str = nav_block_end_crlf if nav_block_end_crlf in content else nav_block_end

# Extract the block
pre_nav, rest = content.split(nav_block_start, 1)
nav_body, post_nav = rest.split(end_str, 1)
full_nav_block = nav_block_start + nav_body + end_str

# Clean isJdEditorOpen out of the nav block
cleaned_nav_block = full_nav_block.replace(
    '        if (isJdEditorOpen) {\n          setIsJdEditorOpen(false);\n          return;\n        }\n', ''
).replace(
    '        if (isJdEditorOpen) {\r\n          setIsJdEditorOpen(false);\r\n          return;\r\n        }\r\n', ''
).replace(
    '    isJdEditorOpen,\n', ''
).replace(
    '    isJdEditorOpen,\r\n', ''
)

# Remove full_nav_block from its old location
content_without_nav = pre_nav.rstrip() + ('\r\n\r\n' if is_crlf else '\n\n') + post_nav.lstrip()

# Find the insertion point: right after line 870 (after queryCandidates sync useEffect)
insert_target = '    if (Array.isArray(queryCandidates) && queryCandidates.length > 0) {\n      setCandidateList((prev) => {\n        if (!prev || prev.length === 0) return queryCandidates;\n        const selectedSet = new Set(prev.filter((c) => c.selected).map((c) => c.id || c.canonical_url));\n        return queryCandidates.map((c) => ({\n          ...c,\n          selected: selectedSet.has(c.id || c.canonical_url),\n        }));\n      });\n    }\n  }, [queryCandidates]);'

insert_target_crlf = insert_target.replace('\n', '\r\n')

if insert_target in content_without_nav:
    new_content = content_without_nav.replace(
        insert_target,
        insert_target + '\n\n' + cleaned_nav_block
    )
elif insert_target_crlf in content_without_nav:
    new_content = content_without_nav.replace(
        insert_target_crlf,
        insert_target_crlf + '\r\n\r\n' + cleaned_nav_block
    )
else:
    raise Exception("insert_target not found in content!")

with open('frontend/src/app/page.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully moved navigation block after candidateList and state declarations!")

