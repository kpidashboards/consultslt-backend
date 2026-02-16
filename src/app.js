require('dotenv').config()
const express = require('express')
const mongoose = require('mongoose')
const cors = require('cors')

const auditoria = require('./middleware/auditoria')

const app = express()

mongoose.connect('mongodb://localhost:27017/consultslt_db')
  .then(() => console.log('✅ MongoDB conectado: consultslt_db'))
  .catch(err => console.error('❌ Erro MongoDB', err))

app.use(cors())
app.use(express.json())
app.use(auditoria)

/* ROTAS */
app.use('/empresas', require('./routes/empresas'))
app.use('/ocr', require('./routes/ocr'))
app.use('/dashboard', require('./routes/dashboard'))
app.use('/fiscal', require('./routes/fiscal'))

app.listen(3000, () =>
  console.log('🚀 API rodando em http://localhost:3000')
)
