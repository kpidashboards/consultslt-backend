const mongoose = require('mongoose')

module.exports = mongoose.model('documentos', new mongoose.Schema({
  empresaId: mongoose.Schema.Types.ObjectId,
  nome: String,
  arquivo: String,
  status: String,
  resultadoOCR: String,
  dataUpload: { type: Date, default: Date.now }
}))