const mongoose = require('mongoose')

module.exports = mongoose.model('empresas', new mongoose.Schema({
  nome: String,
  cnpj: String,
  regime: String,
  status: String
}))