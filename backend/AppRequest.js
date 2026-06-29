const mongoose = require('mongoose');
const AppRequestSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    appName: String,
    url: String,
    color: String,
    status: { type: String, default: 'Pending' }, // Pending, Processing, Completed
    platform: String, // Android, iOS, PC
    createdAt: { type: Date, default: Date.now }
});
module.exports = mongoose.model('AppRequest', AppRequestSchema);
