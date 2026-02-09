# Claude Code Guidelines

How Claude Code should interact with this project.

## Code Modifications

- **Don't remove/modify existing comments** without explicit permission
- Don't refactor code beyond the scope of the task
- Don't add features not explicitly requested
- Only make changes that are directly requested or clearly necessary
- Keep solutions simple and focused

## Project Structure

- Always ask before making changes to project structure or organization
- Don't create unnecessary files or directories
- Don't delete files without asking first

## Scope & Limitations

- For research/exploration tasks, gather information but don't make changes without direction
- If blocked or encountering errors, ask for clarification rather than working around them
- Defer to user judgment about task complexity or feasibility

## Communication

- Reference code with file paths: `filename.ts:42` format
- Be concise and direct
- Flag any security concerns immediately
- Ask before committing significant changes
- **Call out incorrect assumptions directly.** If the user says something patently incorrect (file doesn't exist, requirement already done, etc.), state it plainly rather than pretending to verify. No need to run checks that will obviously fail.

## Working with Comments & Documentation

- Preserve all user-added comments
- Don't add docstrings/comments to code you didn't write
- Only add comments where logic isn't self-evident
- Update comments if code changes that they describe