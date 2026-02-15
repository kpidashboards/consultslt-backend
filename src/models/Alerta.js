const mongoose = require('mongoose')

module.exports = mongoose.model('alertas', new mongoose.Schema({
  empresaId: mongoose.Schema.Types.ObjectId,
  mensagem: String,
  status: String,
  dataCriacao: Date
}))