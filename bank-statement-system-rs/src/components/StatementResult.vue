<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
});

// Dynamic import for opener
async function openOutputFile() {
  if (props.result && props.result.output_path) {
    try {
      console.log("Trying to open file:", props.result.output_path);
      const openerModule = await import('@tauri-apps/plugin-opener');
      
      const openFn = openerModule.openPath || openerModule.open || (openerModule.default && openerModule.default.openPath);
      
      if (typeof openFn === 'function') {
        await openFn(props.result.output_path);
        console.log("File opened successfully");
      } else {
         throw new Error("Could not find 'openPath' function. Available keys: " + Object.keys(openerModule).join(", "));
      }

    } catch (e) {
      console.error("Failed to open file:", e);
      alert("无法打开文件 (Plugin Error): " + e);
    }
  }
}

function formatCurrency(num) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(num);
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-');
}

// Table State
const searchQuery = ref("");
const sortKey = ref("date");
const sortOrder = ref("asc");
const filterBank = ref("all");

// Computed: Get Unique Banks for Filter
const uniqueBanks = computed(() => {
  if (!props.result.records || !props.result.records.length) return [];
  const banks = new Set(props.result.records.map(r => r.bank_name));
  return Array.from(banks).sort();
});

// Computed: Filtered and Sorted Records
const filteredRecords = computed(() => {
  let records = [...(props.result.records || [])];

  // 1. Filter by Bank
  if (filterBank.value !== "all") {
    records = records.filter(r => r.bank_name === filterBank.value);
  }

  // 2. Search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    records = records.filter(r => 
      r.remark.toLowerCase().includes(query) || 
      r.bank_name.toLowerCase().includes(query) ||
      r.debit.toString().includes(query) ||
      r.credit.toString().includes(query)
    );
  }

  // 3. Sort
  records.sort((a, b) => {
    let valA = a[sortKey.value];
    let valB = b[sortKey.value];
    
    if (valA < valB) return sortOrder.value === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder.value === "asc" ? 1 : -1;
    return 0;
  });

  return records;
});

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = key;
    sortOrder.value = "asc";
  }
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Result Summary Card -->
    <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-green-100">
      <div class="bg-green-50 px-6 py-4 border-b border-green-100 flex justify-between items-center">
        <h3 class="text-lg font-bold text-green-800 flex items-center gap-2">
          <span>✅</span> 处理成功
        </h3>
        <!-- Note: Showing current time might be misleading for history view, so we check if result has a timestamp or just hide it -->
        <span class="text-sm text-green-600 bg-green-100 px-3 py-1 rounded-full" v-if="result.created_at">{{ formatDate(result.created_at) }}</span>
      </div>
      
      <div class="p-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="bg-gray-50 rounded-xl p-5 text-center border border-gray-100">
            <p class="text-sm text-gray-500 mb-1">有效记录数</p>
            <p class="text-3xl font-extrabold text-gray-800">{{ result.records_count }} <span class="text-sm text-gray-400 font-normal">条</span></p>
          </div>
          <div class="bg-blue-50 rounded-xl p-5 text-center border border-blue-100">
            <p class="text-sm text-blue-600 mb-1">借方总金额</p>
            <p class="text-2xl font-bold text-blue-900">{{ formatCurrency(result.total_debit) }}</p>
          </div>
          <div class="bg-red-50 rounded-xl p-5 text-center border border-red-100">
            <p class="text-sm text-red-600 mb-1">贷方总金额</p>
            <p class="text-2xl font-bold text-red-900">{{ formatCurrency(result.total_credit) }}</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 flex items-center justify-between border border-gray-200">
          <div class="flex items-center gap-3 overflow-hidden flex-1 mr-4">
            <div class="flex-shrink-0 w-10 h-10 bg-white rounded-lg border border-gray-200 flex items-center justify-center">
              <span class="text-2xl">📄</span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-xs text-gray-500">文件已保存至</p>
              <div class="flex items-center gap-2">
                <p class="text-sm font-medium text-gray-800 truncate" :title="result.output_path">{{ result.output_path }}</p>
              </div>
            </div>
          </div>
          
          <button 
              @click="openOutputFile"
              class="flex-shrink-0 bg-white border border-blue-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300 px-4 py-2 rounded-lg text-sm font-semibold shadow-sm transition-all flex items-center gap-2 active:scale-95"
          >
              <span>📂</span> 打开表格
          </button>
        </div>
      </div>
    </div>

    <!-- Detail Data Table -->
    <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col">
      <!-- Toolbar -->
      <div class="p-4 border-b border-gray-100 flex flex-col md:flex-row gap-4 justify-between items-center bg-gray-50/50">
        <div class="flex items-center gap-2 w-full md:w-auto">
          <span class="text-sm font-semibold text-gray-600">明细数据</span>
          <span class="px-2 py-0.5 rounded-full bg-gray-200 text-xs text-gray-600 font-mono">{{ filteredRecords.length }}</span>
        </div>
        
        <div class="flex gap-3 w-full md:w-auto">
          <!-- Bank Filter -->
          <select v-model="filterBank" class="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
            <option value="all">所有银行</option>
            <option v-for="bank in uniqueBanks" :key="bank" :value="bank">{{ bank }}</option>
          </select>

          <!-- Search -->
          <div class="relative flex-1 md:w-64">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索备注、金额、账号..." 
              class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table class="min-w-full divide-y divide-gray-100 relative">
          <thead class="bg-gray-50/80 sticky top-0 z-10 backdrop-blur-sm">
            <tr>
              <th @click="toggleSort('date')" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none group">
                日期
                <span class="inline-block ml-1 transition-transform" :class="{'rotate-180': sortKey === 'date' && sortOrder === 'desc', 'opacity-0 group-hover:opacity-50': sortKey !== 'date'}">↓</span>
              </th>
              <th @click="toggleSort('bank_name')" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none group">
                银行
                <span class="inline-block ml-1 transition-transform" :class="{'rotate-180': sortKey === 'bank_name' && sortOrder === 'desc', 'opacity-0 group-hover:opacity-50': sortKey !== 'bank_name'}">↓</span>
              </th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                摘要
              </th>
              <th @click="toggleSort('debit')" class="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none group">
                借方
                <span class="inline-block ml-1 transition-transform" :class="{'rotate-180': sortKey === 'debit' && sortOrder === 'desc', 'opacity-0 group-hover:opacity-50': sortKey !== 'debit'}">↓</span>
              </th>
              <th @click="toggleSort('credit')" class="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none group">
                贷方
                <span class="inline-block ml-1 transition-transform" :class="{'rotate-180': sortKey === 'credit' && sortOrder === 'desc', 'opacity-0 group-hover:opacity-50': sortKey !== 'credit'}">↓</span>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50 bg-white">
            <tr v-for="(record, index) in filteredRecords" :key="index" class="hover:bg-blue-50/30 transition-colors">
              <td class="px-6 py-3 whitespace-nowrap text-sm text-gray-500 font-mono">{{ record.date }}</td>
              <td class="px-6 py-3 whitespace-nowrap text-sm font-medium text-gray-700">{{ record.bank_name }}</td>
              <td class="px-6 py-3 text-sm text-gray-600 max-w-xs truncate" :title="record.remark">{{ record.remark }}</td>
              <td class="px-6 py-3 whitespace-nowrap text-sm text-right font-medium text-blue-600" :class="{'opacity-20': record.debit === 0}">
                {{ record.debit !== 0 ? formatCurrency(record.debit) : '-' }}
              </td>
              <td class="px-6 py-3 whitespace-nowrap text-sm text-right font-medium text-red-600" :class="{'opacity-20': record.credit === 0}">
                {{ record.credit !== 0 ? formatCurrency(record.credit) : '-' }}
              </td>
            </tr>
            <tr v-if="filteredRecords.length === 0">
              <td colspan="5" class="px-6 py-12 text-center text-gray-400 text-sm">
                没有找到匹配的记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Custom Scrollbar for Table */
.overflow-x-auto::-webkit-scrollbar,
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.overflow-x-auto::-webkit-scrollbar-track,
.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.overflow-x-auto::-webkit-scrollbar-thumb,
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.overflow-x-auto::-webkit-scrollbar-thumb:hover,
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
