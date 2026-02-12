# Tabela de Tecnologias e Versões

| Tecnologia         | Versão/Revisão         | Observação                      |
|--------------------|------------------------|----------------------------------|
| Python             | >=3.9                  | Backend                         |
| FastAPI            | >=0.78                 | Framework API                    |
| Motor (MongoDB)    | >=2.5                  | Driver assíncrono MongoDB        |
| MongoDB            | >=4.4                  | Banco de dados                   |
| Docker Compose     | >=1.29                 | Orquestração local               |
| passlib[bcrypt]    | >=1.7                  | Hash de senha                    |
| PyJWT              | >=2.0                  | Autenticação JWT                 |
| Uvicorn            | >=0.17                 | ASGI server                      |
| Pydantic           | >=1.10                 | Schemas/validação                |
| React              | >=17                   | Frontend                         |
| TailwindCSS        | >=3                    | Frontend                         |
| Node.js            | >=16                   | Frontend                         |
| Yarn/NPM           | >=1.22/8               | Frontend                         |
| Outros             | -                      | Vide requirements.txt/package.json|

---

- Todas as dependências backend estão em requirements.txt
- Todas as dependências frontend estão em package.json
- Infraestrutura dockerizada para desenvolvimento e produção
