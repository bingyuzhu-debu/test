<script setup>
import { ref } from 'vue';
import Generator from './components/Generator.vue';
import History from './components/History.vue';

const currentView = ref('generator');
</script>

<template>
  <div class="flex h-screen bg-gray-50 font-sans antialiased text-gray-900">
    <!-- Sidebar -->
    <aside class="w-72 bg-slate-900 text-white flex flex-col shadow-2xl z-20">
      <div class="p-8 border-b border-slate-800">
        <h1 class="text-2xl font-extrabold tracking-tight flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-300">
          <span class="text-3xl filter drop-shadow-lg">🏦</span> 
          <span>对账助手</span>
        </h1>
        <p class="text-slate-400 text-xs mt-3 font-medium tracking-wide uppercase opacity-70">Finance Automation Pro</p>
      </div>
      
      <nav class="flex-1 px-4 py-8 space-y-3">
        <button 
          @click="currentView = 'generator'"
          :class="[
            'w-full text-left px-5 py-4 rounded-xl transition-all duration-300 flex items-center gap-4 font-medium group',
            currentView === 'generator' 
              ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30 translate-x-1' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white hover:translate-x-1'
          ]"
        >
          <span class="text-xl group-hover:scale-110 transition-transform duration-300">⚡</span> 
          <span>开始生成</span>
        </button>
        
        <button 
          @click="currentView = 'history'"
          :class="[
            'w-full text-left px-5 py-4 rounded-xl transition-all duration-300 flex items-center gap-4 font-medium group',
            currentView === 'history' 
              ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30 translate-x-1' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white hover:translate-x-1'
          ]"
        >
          <span class="text-xl group-hover:scale-110 transition-transform duration-300">📜</span> 
          <span>历史记录</span>
        </button>
      </nav>

      <div class="p-6 border-t border-slate-800">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-xs font-bold">
            FN
          </div>
          <div>
            <p class="text-sm font-medium text-white">财务部专用</p>
            <p class="text-xs text-slate-500">v1.2.0 Stable</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto bg-gray-50 relative">
      <!-- Decorative Background Elements -->
      <div class="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-blue-50 to-transparent pointer-events-none"></div>

      <div class="relative p-10 max-w-7xl mx-auto">
        <Transition name="fade" mode="out-in">
          <KeepAlive>
            <component :is="currentView === 'generator' ? Generator : History" />
          </KeepAlive>
        </Transition>
      </div>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
</style>
