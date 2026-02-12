
        logger.exception("Erro no health check do MongoDB")
        result["checks"]["mongodb"] = {
            "status": "error",
            "error": str(e)
        }
        result["status"] = "degraded"

    return result
