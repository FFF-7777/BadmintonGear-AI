import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { setupGlobalErrorHandler } from './utils/error-report'
import './styles/ios.css'
import './styles/markdown.css'

const app = createApp(App)
app.use(router)
setupGlobalErrorHandler(app)
app.mount('#app')
