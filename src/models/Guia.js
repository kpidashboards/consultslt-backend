const mongoose = require('mongoose')

module.exports = mongoose.model('guias', new mongoose.Schema({
  empresaId: mongoose.Schema.Types.ObjectId,
  periodo: String,
  valor: Number,
  status: String,
  dataEmissao: Date
}))