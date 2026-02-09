# Coding Conventions

## Python (FastAPI)
- Use Pydantic models for all request/response schemas
- Type hints required (including return types and imports)
- Max line length: 150 chars
- Use `async/await` for all endpoints
- Error handling: raise HTTPException with proper status codes
- Prefer explicit properties/attributes with type hints (e.g., `self.engine: AsyncEngine | None = None`)
- **When defining `@property` decorators, always include corresponding `@property_name.setter` methods** to allow assignment
- Async generator functions must return `AsyncGenerator[YieldType, None]` not just the yield type

## Go
- Follow standard Go formatting (gofmt)
- Use context.Context for all handlers
- Error handling: explicit error returns, log before returning
- Use structured logging (zerolog or similar)

## React/TypeScript
- Functional components only (no classes)
- TypeScript strict mode enabled
- Use React Query for API calls
- Tailwind CSS for styling

## General
- Write tests for business logic (aim for >90% coverage)