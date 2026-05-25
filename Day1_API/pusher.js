const axios = require('axios');

// Switch localhost to 127.0.0.1 to avoid local routing bugs
const API_URL = 'http://127.0.0.1:5000/api/items';

const dummyDataBatch = [
    { name: "Wireless Mouse", category: "Electronics", quantity: 150 },
    { name: "Mechanical Keyboard", category: "Electronics", quantity: 45 },
    { name: "Running Shoes", category: "Apparel", quantity: 30 },
    { name: "Coffee Mug", category: "Kitchenware", quantity: 85 }
];

async function pushData() {
    console.log("Starting data push to MongoDB...");
    
    for (const item of dummyDataBatch) {
        try {
            const response = await axios.post(API_URL, item);
            console.log(`Successfully pushed: ${response.data.name}`);
        } catch (error) {
            // This will give us the direct error code (like ECONNREFUSED)
            console.error(`Failed to push ${item.name}. Code: ${error.code || error.message}`);
        }
    }
    
    console.log("Data push sequence complete!");
}

pushData();