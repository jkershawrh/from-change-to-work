"""Existing EVY gateway with a narrow external surface for this handoff."""
from fastapi.responses import JSONResponse
from backend.api_gateway.main import app
@app.middleware('http')
async def action_surface_only(request,call_next):
 if request.url.path!='/health' and not request.url.path.startswith('/actions/'):
  return JSONResponse({'detail':'NOT_FOUND'},status_code=404)
 return await call_next(request)
