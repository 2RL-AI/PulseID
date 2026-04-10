import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

import LandingPage from "../views/LandingPage.vue";
import LoginPage from "../views/LoginPage.vue";
import DashboardLayout from "../components/DashboardLayout.vue";
import EmployeesPage from "../views/EmployeesPage.vue";
import BadgesPage from "../views/BadgesPage.vue";
import RecordsPage from "../views/RecordsPage.vue";
import UsersPage from "../views/UsersPage.vue";
import OfficePage from "../views/OfficePage.vue";
import DatabasePage from "../views/DatabasePage.vue";

const routes = [
  { path: "/", name: "landing", component: LandingPage },
  { path: "/login", name: "login", component: LoginPage },
  {
    path: "/dashboard",
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "", redirect: { name: "employees" } },
      { path: "employees", name: "employees", component: EmployeesPage },
      { path: "badges", name: "badges", component: BadgesPage },
      { path: "records", name: "records", component: RecordsPage },
      { path: "users", name: "users", component: UsersPage },
      { path: "office", name: "office", component: OfficePage },
      { path: "database", name: "database", component: DatabasePage },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth || to.matched.some((r) => r.meta.requiresAuth)) {
    const auth = useAuthStore();
    if (!auth.isAuthenticated) {
      return { name: "login", query: { redirect: to.fullPath } };
    }
  }
});

export default router;
