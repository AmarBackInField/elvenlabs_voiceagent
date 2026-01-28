"""
Ecommerce integration for voice agents.
Supports WooCommerce, Shopify, and other platforms dynamically.
"""

import logging
from typing import Optional, Dict, Any, List
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("elevenlabs.ecommerce")


class EcommerceClient:
    """
    Client for ecommerce platforms (WooCommerce, Shopify, etc.)
    """
    
    SUPPORTED_PLATFORMS = ["woocommerce", "shopify"]
    
    def __init__(
        self, 
        platform: str,
        base_url: str, 
        api_key: str, 
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None
    ):
        """
        Initialize ecommerce client.
        
        Args:
            platform: Platform name ("woocommerce", "shopify", etc.)
            base_url: Base API URL
            api_key: API key / Consumer key
            api_secret: API secret (for WooCommerce)
            access_token: Access token (for Shopify, etc.)
        """
        self.platform = platform.lower()
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        
        if self.platform not in self.SUPPORTED_PLATFORMS:
            logger.warning(f"Platform '{self.platform}' may not be fully supported")
        
        logger.info(f"EcommerceClient initialized for {self.platform}")
    
    def get_products(self, limit: int = 5) -> Dict[str, Any]:
        """
        Fetch products from the ecommerce store.
        
        Args:
            limit: Number of products to fetch (default: 5)
            
        Returns:
            Dict with products list and formatted text
        """
        try:
            logger.info(f"Fetching {limit} products from {self.platform}...")
            
            if self.platform == "woocommerce":
                return self._get_woocommerce_products(limit)
            elif self.platform == "shopify":
                return self._get_shopify_products(limit)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{self.platform}' is not supported yet.",
                    "products": []
                }
                
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": []
            }
    
    def get_orders(self, limit: int = 5) -> Dict[str, Any]:
        """
        Fetch recent orders from the ecommerce store.
        
        Args:
            limit: Number of orders to fetch (default: 5)
            
        Returns:
            Dict with orders list and formatted text
        """
        try:
            logger.info(f"Fetching {limit} orders from {self.platform}...")
            
            if self.platform == "woocommerce":
                return self._get_woocommerce_orders(limit)
            elif self.platform == "shopify":
                return self._get_shopify_orders(limit)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{self.platform}' is not supported yet.",
                    "orders": []
                }
                
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return {
                "success": False,
                "error": str(e),
                "orders": []
            }
    
    def _get_woocommerce_products(self, limit: int) -> Dict[str, Any]:
        """Fetch products from WooCommerce."""
        url = f"{self.base_url}/wp-json/wc/v3/products"
        params = {"per_page": limit}
        auth = HTTPBasicAuth(self.api_key, self.api_secret or "")
        
        # Debug logging
        logger.info(f"WooCommerce API Request:")
        logger.info(f"  URL: {url}")
        logger.info(f"  API Key: {self.api_key[:10]}..." if self.api_key else "  API Key: None")
        logger.info(f"  API Secret: {'*' * 10}" if self.api_secret else "  API Secret: None")
        
        response = requests.get(url, auth=auth, params=params, timeout=30)
        logger.info(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            products = response.json()
            formatted = self._format_woocommerce_products(products)
            return {
                "success": True,
                "products": products,
                "formatted": formatted,
                "count": len(products)
            }
        else:
            logger.error(f"Failed to fetch products: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "products": []
            }
    
    def _get_woocommerce_orders(self, limit: int) -> Dict[str, Any]:
        """Fetch orders from WooCommerce."""
        url = f"{self.base_url}/wp-json/wc/v3/orders"
        params = {"per_page": limit}
        auth = HTTPBasicAuth(self.api_key, self.api_secret or "")
        
        response = requests.get(url, auth=auth, params=params, timeout=30)
        
        if response.status_code == 200:
            orders = response.json()
            formatted = self._format_woocommerce_orders(orders)
            return {
                "success": True,
                "orders": orders,
                "formatted": formatted,
                "count": len(orders)
            }
        else:
            logger.error(f"Failed to fetch orders: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "orders": []
            }
    
    def _get_shopify_products(self, limit: int) -> Dict[str, Any]:
        """Fetch products from Shopify."""
        url = f"{self.base_url}/admin/api/2024-01/products.json"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        params = {"limit": limit}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            formatted = self._format_shopify_products(products)
            return {
                "success": True,
                "products": products,
                "formatted": formatted,
                "count": len(products)
            }
        else:
            logger.error(f"Failed to fetch products: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "products": []
            }
    
    def _get_shopify_orders(self, limit: int) -> Dict[str, Any]:
        """Fetch orders from Shopify."""
        url = f"{self.base_url}/admin/api/2024-01/orders.json"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        params = {"limit": limit, "status": "any"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            formatted = self._format_shopify_orders(orders)
            return {
                "success": True,
                "orders": orders,
                "formatted": formatted,
                "count": len(orders)
            }
        else:
            logger.error(f"Failed to fetch orders: {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "orders": []
            }
    
    def _format_woocommerce_products(self, products: List[Dict]) -> str:
        """Format WooCommerce products into readable text."""
        if not products:
            return "No products found."
        
        result = f"Found {len(products)} products:\n"
        for p in products:
            name = p.get('name', 'Unknown')
            price = p.get('price', '0')
            stock_status = p.get('stock_status', 'unknown')
            sku = p.get('sku', 'N/A')
            result += f"\n- {name}\n"
            result += f"  Price: ${price}\n"
            result += f"  SKU: {sku}\n"
            result += f"  Stock: {stock_status}\n"
        
        return result
    
    def _format_woocommerce_orders(self, orders: List[Dict]) -> str:
        """Format WooCommerce orders into readable text."""
        if not orders:
            return "No orders found."
        
        result = f"Found {len(orders)} recent orders:\n"
        for o in orders:
            order_id = o.get('id', 'Unknown')
            status = o.get('status', 'unknown')
            total = o.get('total', '0')
            date = o.get('date_created', 'Unknown')
            customer = o.get('billing', {})
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            result += f"\n- Order #{order_id}\n"
            result += f"  Customer: {customer_name or 'Unknown'}\n"
            result += f"  Status: {status}\n"
            result += f"  Total: ${total}\n"
            result += f"  Date: {date}\n"
        
        return result
    
    def _format_shopify_products(self, products: List[Dict]) -> str:
        """Format Shopify products into readable text."""
        if not products:
            return "No products found."
        
        result = f"Found {len(products)} products:\n"
        for p in products:
            title = p.get('title', 'Unknown')
            variants = p.get('variants', [])
            price = variants[0].get('price', '0') if variants else '0'
            inventory = variants[0].get('inventory_quantity', 0) if variants else 0
            result += f"\n- {title}\n"
            result += f"  Price: ${price}\n"
            result += f"  Inventory: {inventory}\n"
        
        return result
    
    def _format_shopify_orders(self, orders: List[Dict]) -> str:
        """Format Shopify orders into readable text."""
        if not orders:
            return "No orders found."
        
        result = f"Found {len(orders)} recent orders:\n"
        for o in orders:
            name = o.get('name', 'Unknown')
            status = o.get('financial_status', 'unknown')
            fulfillment = o.get('fulfillment_status', 'unfulfilled') or 'unfulfilled'
            total = o.get('total_price', '0')
            customer = o.get('customer', {})
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            result += f"\n- Order {name}\n"
            result += f"  Customer: {customer_name or 'Unknown'}\n"
            result += f"  Payment: {status}\n"
            result += f"  Fulfillment: {fulfillment}\n"
            result += f"  Total: ${total}\n"
        
        return result


class EcommerceService:
    """
    Service for managing ecommerce operations within calls.
    """
    
    def __init__(self):
        """Initialize ecommerce service."""
        self._clients: Dict[str, EcommerceClient] = {}
        logger.info("EcommerceService initialized")
    
    def create_client(
        self,
        session_id: str,
        platform: str,
        base_url: str,
        api_key: str,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> EcommerceClient:
        """
        Create an ecommerce client for a specific session/call.
        
        Args:
            session_id: Unique session identifier (e.g., conversation_id)
            platform: Platform name
            base_url: Base API URL
            api_key: API key
            api_secret: API secret (for WooCommerce)
            access_token: Access token (for Shopify)
            
        Returns:
            EcommerceClient instance
        """
        client = EcommerceClient(
            platform=platform,
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token
        )
        self._clients[session_id] = client
        logger.info(f"Created ecommerce client for session {session_id}")
        return client
    
    def get_client(self, session_id: str) -> Optional[EcommerceClient]:
        """Get ecommerce client for a session."""
        return self._clients.get(session_id)
    
    def remove_client(self, session_id: str):
        """Remove ecommerce client for a session."""
        if session_id in self._clients:
            del self._clients[session_id]
            logger.info(f"Removed ecommerce client for session {session_id}")
    
    def get_products(
        self,
        session_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch products for a session.
        
        Args:
            session_id: Session identifier
            limit: Number of products to fetch
            
        Returns:
            Products result dict
        """
        client = self.get_client(session_id)
        if not client:
            return {
                "success": False,
                "error": "No ecommerce platform connected for this session",
                "products": []
            }
        
        return client.get_products(limit=min(limit, 20))
    
    def get_orders(
        self,
        session_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch orders for a session.
        
        Args:
            session_id: Session identifier
            limit: Number of orders to fetch
            
        Returns:
            Orders result dict
        """
        client = self.get_client(session_id)
        if not client:
            return {
                "success": False,
                "error": "No ecommerce platform connected for this session",
                "orders": []
            }
        
        return client.get_orders(limit=min(limit, 20))


# Global service instance
_ecommerce_service: Optional[EcommerceService] = None


def get_ecommerce_service() -> EcommerceService:
    """Get or create the global ecommerce service."""
    global _ecommerce_service
    if _ecommerce_service is None:
        _ecommerce_service = EcommerceService()
    return _ecommerce_service


# =============================================================================
# Batch Job Context Store
# =============================================================================

class BatchJobContextStore:
    """
    Store for batch job context (e-commerce credentials, recipient info).
    Used to look up context when webhook calls come in from batch jobs.
    """
    
    def __init__(self):
        """Initialize batch job context store."""
        # job_id -> {ecommerce_credentials, sender_email, agent_id}
        self._jobs: Dict[str, Dict[str, Any]] = {}
        # agent_id -> job_id (most recent)
        self._agent_jobs: Dict[str, str] = {}
        # phone_number -> {name, email, job_id}
        self._recipients: Dict[str, Dict[str, Any]] = {}
        logger.info("BatchJobContextStore initialized")
    
    def store_job(
        self,
        job_id: str,
        agent_id: str,
        ecommerce_credentials: Optional[Dict[str, Any]] = None,
        sender_email: Optional[str] = None,
        recipients: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Store batch job context.
        
        Args:
            job_id: Batch job ID
            agent_id: Agent ID handling the calls
            ecommerce_credentials: E-commerce platform credentials
            sender_email: Sender email for email templates
            recipients: List of recipients with name/email
        """
        self._jobs[job_id] = {
            "agent_id": agent_id,
            "ecommerce_credentials": ecommerce_credentials,
            "sender_email": sender_email
        }
        self._agent_jobs[agent_id] = job_id
        
        # Store recipient info by phone number
        if recipients:
            for r in recipients:
                phone = r.get("phone_number")
                if phone:
                    self._recipients[phone] = {
                        "name": r.get("name"),
                        "email": r.get("email"),
                        "job_id": job_id,
                        "agent_id": agent_id
                    }
        
        logger.info(f"Stored batch job context: job_id={job_id}, agent_id={agent_id}, recipients={len(recipients or [])}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job context by job ID."""
        return self._jobs.get(job_id)
    
    def get_job_by_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get most recent batch job context by agent ID."""
        job_id = self._agent_jobs.get(agent_id)
        if job_id:
            job = self._jobs.get(job_id)
            if job:
                job["job_id"] = job_id
                return job
        return None
    
    def get_recipient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get recipient info by phone number."""
        return self._recipients.get(phone_number)
    
    def get_ecommerce_credentials(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get e-commerce credentials for an agent's batch job."""
        job = self.get_job_by_agent(agent_id)
        if job:
            return job.get("ecommerce_credentials")
        return None
    
    def get_sender_email(self, agent_id: str) -> Optional[str]:
        """Get sender email for an agent's batch job."""
        job = self.get_job_by_agent(agent_id)
        if job:
            return job.get("sender_email")
        return None
    
    def remove_job(self, job_id: str) -> None:
        """Remove batch job context."""
        job = self._jobs.get(job_id)
        if job:
            agent_id = job.get("agent_id")
            if agent_id and self._agent_jobs.get(agent_id) == job_id:
                del self._agent_jobs[agent_id]
            del self._jobs[job_id]
            
            # Clean up recipients for this job
            to_remove = [phone for phone, info in self._recipients.items() if info.get("job_id") == job_id]
            for phone in to_remove:
                del self._recipients[phone]
            
            logger.info(f"Removed batch job context: job_id={job_id}")
    
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all batch job contexts (for debugging)."""
        return self._jobs.copy()


# Global batch job context store
_batch_job_context: Optional[BatchJobContextStore] = None


def get_batch_job_context() -> BatchJobContextStore:
    """Get or create the global batch job context store."""
    global _batch_job_context
    if _batch_job_context is None:
        _batch_job_context = BatchJobContextStore()
    return _batch_job_context
