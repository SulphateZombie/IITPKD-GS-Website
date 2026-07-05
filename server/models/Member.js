const mongoose = require('mongoose');

const memberSchema = new mongoose.Schema({
  Name: String,
  Subsystem: String,
  "Hierarchal position": String,
  "Email ID": String,
  "LinkedIN ID": String,
  "Instagram ID": String,
  Photo: String,
  Timestamp: String,
}, { strict: false });

// Mongoose will look for the "members" collection
module.exports = mongoose.model('Member', memberSchema);