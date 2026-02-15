const mongoose = require('mongoose')

const Auditoria = mongoose.model(
  'auditoria',
  new mongoose.Schema({
    acao: String,
    rota: String,
    metodo: String,
    payload: Object,
    data: { type: Date, default: Date.now }
  })
)

module.exports = (req, res, next) => {
  res.on('finish', async () => {
    if (req.method !== 'GET') {
      await Auditoria.create({
        acao: 'CRUD',
        rota: req.originalUrl,
        metodo: req.method,
        payload: req.body
      })
    }
  })
  next()
}
