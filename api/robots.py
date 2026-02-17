from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/robots", tags=["Robôs"])

@router.get("/status", status_code=status.HTTP_200_OK)
async def obter_status():
    """Obtém o status atual dos robôs."""
    return {"status": "ok", "message": "Robôs funcionando corretamente."}

@router.get("/tasks", status_code=status.HTTP_200_OK)
async def listar_tarefas():
    """Lista todas as tarefas em execução pelos robôs."""
    # TODO: Implementar integração com o serviço de tarefas
    return {"tasks": []}

@router.post("/execute", status_code=status.HTTP_201_CREATED)
async def executar_tarefa(tarefa: dict):
    """Executa uma nova tarefa nos robôs."""
    # TODO: Implementar lógica de execução de tarefas
    if not tarefa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tarefa inválida.")
    return {"status": "created", "tarefa": tarefa}

