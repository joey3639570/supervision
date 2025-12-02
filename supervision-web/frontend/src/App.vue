<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>Supervision Web</v-toolbar-title>
      <v-spacer></v-spacer>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" temporary>
      <v-list>
        <v-list-item
          v-for="item in menuItems"
          :key="item.title"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'

const drawer = ref(false)

const menuItems = [
  { title: '首頁', icon: 'mdi-home', to: '/' },
  { title: '物件檢測', icon: 'mdi-target', to: '/detect' },
  { title: '圖像分割', icon: 'mdi-image-edit', to: '/segment' },
  { title: '物件追蹤', icon: 'mdi-video', to: '/track' },
  { title: 'SAM3 演示', icon: 'mdi-robot', to: '/sam3' },
  { title: '標註工具', icon: 'mdi-draw', to: '/annotate' },
  { title: '資料集管理', icon: 'mdi-database', to: '/dataset' },
  { title: '評估指標', icon: 'mdi-chart-line', to: '/metrics' },
  { title: '區域分析', icon: 'mdi-map', to: '/geometry' },
  { title: '影片處理', icon: 'mdi-film', to: '/video' },
]
</script>



