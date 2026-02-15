const mongoose = require('mongoose')

module.exports = mongoose.model('obrigacoes', new mongoose.Schema({
  empresaId: mongoose.Schema.Types.ObjectId,
  tipo: String,
  vencimento: Date,
  status: String,
  valor: Number
}))