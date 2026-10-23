"""Opt-in EVY API action registration. Operator/viewer credentials stay server-side."""
from fastapi import APIRouter,Request,HTTPException
from backend.actions.capability_transfer import ActionDispatcher,ActionError,MAX_REQUEST,parse_intent
router=APIRouter(prefix='/actions',tags=['capability-actions'])

def configured(request,write=False):
    try:
        dispatcher=ActionDispatcher.from_environment()
        header=request.headers.get('authorization','')
        if not header.startswith('Bearer '):raise ActionError('AUTH_REQUIRED',401)
        dispatcher.authorize(header[7:],write=write)
        return dispatcher
    except ActionError as e:raise HTTPException(e.status,e.code) from None

@router.get('/catalog')
async def catalog(request:Request):return configured(request).catalog()

@router.post('/capability-transfer',status_code=202)
async def submit(request:Request):
    dispatcher=configured(request,write=True)
    try:
        data=bytearray()
        async for block in request.stream():
            data.extend(block)
            if len(data)>MAX_REQUEST:raise ActionError('BODY_LIMIT',413)
        return await dispatcher.dispatch(parse_intent(bytes(data)))
    except ActionError as e:raise HTTPException(e.status,e.code) from None

@router.get('/capability-transfer/{action_id}')
async def observe(action_id:str,request:Request):
    dispatcher=configured(request)
    try:return await dispatcher.status(action_id)
    except ActionError as e:raise HTTPException(e.status,e.code) from None
