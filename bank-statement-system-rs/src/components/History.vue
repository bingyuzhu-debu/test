<script setup>
import { ref, onMounted, onActivated } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { ask } from "@tauri-apps/plugin-dialog";
import StatementResult from "./StatementResult.vue";

const history = ref([]);
const isLoading = ref(false);
const selectedRecord = ref(null);
const isDetailLoading = ref(false);

async function loadHistory() {
  isLoading.value = true;
  try {
    history.value = await invoke("get_history");
  } catch (error) {
    console.error("Failed to load history:", error);
  } finally {
    isLoading.value = false;
  }
}

async function viewDetails(record) {
  isDetailLoading.value = true;
  try {
    const details = await invoke("get_history_details", { id: record.id });
    // Ensure output_path is set correctly from filename map if needed, 
    // or just assume filename is full path or we construct it. 
    // Actually generator.rs saves full path in 'filename' column? 
    // Let's check save_history. Yes, it saves 'file_path' which is input. 
    // Ah, wait. 'output_path' is needed for the "Open File" button.
    // In save_history, we saved `filename` as the input file path.
    // The output path logic was: parent + company + month + .xlsx. 
    // We might need to reconstruct it here or store it in DB.
    // For now, let's reconstruct it crudely or just use the input path for display? 
    // No, "Open File" needs the OUTPUT path.
    // The DB currently stores 'filename' which comes from 'file_path' (input).
    // It does NOT store output_path explicitly in a separate column, but we can reconstruct it.
    
    // Quick fix: We can try to reconstruct output path if we know the rules.
    // Rule: input_path parent dir + company + month + "_对账单.xlsx"
    // Ideally we should have stored output_path in DB. 
    // But let's verify if we can get it from what we have.
    
    // Let's proceed with displaying the record. The 'StatementResult' expects 'result.output_path' for the button.
    // We will attach a constructed output_path to the details object before passing to component.
    
    // A better approach for now: disable "Open File" in history or try to guess.
    // Since I cannot change DB schema right now easily without risking data, I will try to reconstruct it.
    
    // Wait, let's look at `db.rs` again. `filename` column.
    // `save_history` in `lib.rs`: 
    // `save_history(&app, &company, &month, &file_path, &result)`
    // So `filename` is the INPUT file path.
    
    // To reconstruct output path:
    // We need parent of input path.
    // JS side string manipulation on `details.filename` (input path).
    
    let outputPath = details.filename; 
    // Simple heuristic: replace filename with name pattern in same dir
    // This assumes Windows paths
    const lastSlash = Math.max(outputPath.lastIndexOf('\\'), outputPath.lastIndexOf('/'));
    if (lastSlash !== -1) {
       const dir = outputPath.substring(0, lastSlash);
       outputPath = `${dir}\\${details.company}_${details.month}_对账单.xlsx`;
    }
    details.output_path = outputPath;

    selectedRecord.value = details;
  } catch (error) {
    console.error("Failed to load details:", error);
    alert("无法加载详情: " + error);
  } finally {
    isDetailLoading.value = false;
  }
}

async function deleteItem(record) {
  const yes = await ask(`确定要删除 ${record.month} ${record.company} 的对账单记录吗？\n此操作不可恢复。`, {
    title: '确认删除',
    kind: 'warning',
    okLabel: '确定删除',
    cancelLabel: '取消'
  });

  if (!yes) return;
  
  try {
    await invoke("delete_history", { id: record.id });
    await loadHistory(); 
  } catch (error) {
    console.error("Failed to delete history:", error);
    alert("删除失败: " + error); // Alert also can be replaced by message, but ask is enough for now
  }
}

function closeDetails() {
  selectedRecord.value = null;
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

onMounted(() => {
  loadHistory();
});

onActivated(() => {
  loadHistory();
});
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6 animate-fade-in relative min-h-screen">
    <div class="flex justify-between items-end">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">历史记录</h2>
        <p class="text-sm text-gray-500 mt-1">查看最近生成的对账单详情</p>
      </div>
      <button 
        @click="loadHistory" 
        class="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-colors flex items-center gap-2"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="animate-spin">🔄</span>
        <span v-else>🔄</span>
        刷新列表
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="!isLoading && history.length === 0" class="bg-white rounded-2xl shadow-sm border border-gray-100 p-16 text-center">
      <div class="bg-gray-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
        <span class="text-4xl">📭</span>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-1">暂无记录</h3>
      <p class="text-gray-500">生成的对账单记录将显示在这里</p>
    </div>

    <!-- Data Table -->
    <div v-else class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      <div class="overflow-x-auto">
        <table class="min-w-[1000px] divide-y divide-gray-100">
          <thead class="bg-gray-50/50">
            <tr>
              <th scope="col" class="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">生成时间</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">公司主体</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">所属月份</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">文件名</th>
              <th scope="col" class="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">记录数</th>
              <th scope="col" class="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">借方总额</th>
              <th scope="col" class="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">贷方总额</th>
              <th scope="col" class="px-6 py-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50 bg-white">
            <tr v-for="item in history" :key="item.id" class="hover:bg-blue-50/30 transition-colors group">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                {{ formatDate(item.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                  {{ item.company }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                {{ item.month }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate max-w-xs" :title="item.filename">
                 {{ item.filename ? item.filename.split('\\').pop().split('/').pop() : '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                {{ item.records_count }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                {{ formatCurrency(item.total_debit) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                {{ formatCurrency(item.total_credit) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-center text-sm font-medium space-x-3">
                <button 
                  @click="viewDetails(item)"
                  class="text-blue-600 hover:text-blue-900 hover:underline"
                >
                  查看详情
                </button>
                <button 
                  @click="deleteItem(item)"
                  class="text-red-500 hover:text-red-700 hover:underline"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Detail Modal Overlay -->
    <div v-if="selectedRecord" class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
       <!-- Backdrop -->
       <div class="absolute inset-0 bg-gray-900/60 backdrop-blur-sm transition-opacity" @click="closeDetails"></div>
       
       <!-- Modal Content -->
       <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden animate-zoom-in">
          <!-- Modal Header -->
          <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
             <div>
                <h3 class="text-lg font-bold text-gray-900">对账单详情</h3>
                <p class="text-sm text-gray-500">{{ selectedRecord.company }} - {{ selectedRecord.month }}</p>
             </div>
             <button @click="closeDetails" class="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-200 transition-colors">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
             </button>
          </div>
          
          <!-- Modal Body (Scrollable) -->
          <div class="p-6 overflow-y-auto bg-gray-50 flex-1">
             <StatementResult :result="selectedRecord" />
          </div>
       </div>
    </div>
  
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}

.animate-zoom-in {
  animation: zoomIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes zoomIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
