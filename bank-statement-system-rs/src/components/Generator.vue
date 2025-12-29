<script setup>
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import StatementResult from "./StatementResult.vue";

const companies = ["雷石天地", "镭海", "成都雷石"];

const selectedCompany = ref("雷石天地");
const selectedMonth = ref(new Date().toISOString().slice(0, 7)); // YYYY-MM
const selectedFile = ref("");
const isGenerating = ref(false);
const generationResult = ref(null);
const errorMessage = ref("");

async function selectFile() {
  const file = await open({
    multiple: false,
    filters: [{
      name: 'Excel Files',
      extensions: ['xls', 'xlsx']
    }]
  });
  if (file) {
    selectedFile.value = file;
    // Reset result when file changes
    generationResult.value = null;
    errorMessage.value = "";
  }
}

async function startGenerate() {
  if (!selectedFile.value) return;

  isGenerating.value = true;
  generationResult.value = null;
  errorMessage.value = "";

  try {
    const result = await invoke("generate_statement", {
      company: selectedCompany.value,
      month: selectedMonth.value,
      filePath: selectedFile.value
    });

    if (result.success) {
      generationResult.value = result;
    } else {
      errorMessage.value = result.message;
    }
  } catch (error) {
    errorMessage.value = `系统错误: ${error}`;
  } finally {
    isGenerating.value = false;
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-8 animate-fade-in-up pb-12">
    <!-- Header Section -->
    <div class="text-center mb-8">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">对账单生成</h2>
      <p class="mt-2 text-sm text-gray-500">请选择原始 Excel 文件并配置相关信息</p>
    </div>

    <!-- Configuration Card -->
    <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      <div class="p-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- Company & Month -->
          <div class="space-y-6">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">选择公司</label>
              <div class="relative">
                <select v-model="selectedCompany" class="w-full pl-4 pr-10 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none cursor-pointer hover:bg-white">
                  <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
                </select>
                <div class="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none">
                  <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">所属月份</label>
              <input type="month" v-model="selectedMonth" class="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-700 focus:ring-2 focus:ring-blue-500 outline-none transition-all hover:bg-white" />
            </div>
          </div>

          <!-- File Selection -->
          <div class="flex flex-col justify-center">
            <label class="block text-sm font-semibold text-gray-700 mb-2">原始凭证文件</label>
            <div 
              @click="selectFile"
              class="flex-1 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-blue-50 hover:border-blue-400 transition-all cursor-pointer flex flex-col items-center justify-center p-6 group"
            >
              <div v-if="!selectedFile" class="text-center">
                <div class="w-12 h-12 bg-blue-100 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                </div>
                <p class="text-sm text-gray-500 font-medium">点击选择 Excel 文件 (.xls, .xlsx)</p>
              </div>
              
              <div v-else class="text-center w-full">
                <div class="w-12 h-12 bg-green-100 text-green-500 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <p class="text-sm font-bold text-gray-800 break-all px-4 truncate max-w-xs mx-auto">{{ selectedFile.split('\\').pop() }}</p>
                <p class="text-xs text-gray-400 mt-1">点击更换文件</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Button -->
        <div class="mt-8">
          <button 
            @click="startGenerate" 
            :disabled="isGenerating || !selectedFile"
            class="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all flex items-center justify-center gap-3"
          >
            <span v-if="isGenerating" class="animate-spin">⏳</span>
            {{ isGenerating ? '正在处理数据...' : '立即开始生成' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg shadow-sm animate-fade-in">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">生成失败</h3>
          <div class="mt-2 text-sm text-red-700"><p>{{ errorMessage }}</p></div>
        </div>
      </div>
    </div>

    <!-- Result & Data Table -->
    <StatementResult v-if="generationResult" :result="generationResult" />
  </div>
</template>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
