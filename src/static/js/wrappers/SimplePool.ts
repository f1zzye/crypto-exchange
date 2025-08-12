import { Address, beginCell, Cell, Contract, contractAddress, ContractProvider, Sender, SendMode, toNano } from '@ton/core';

export type SimplePoolConfig = {
    admin: Address;
};

export function simplePoolConfigToCell(config: SimplePoolConfig): Cell {
    const emptyAddress = beginCell().storeUint(0, 2).endCell().beginParse();
    
    return beginCell()
        .storeUint(0, 1) // deployed = false
        .storeAddress(config.admin)
        .storeSlice(emptyAddress) // usdt_master (empty)
        .storeUint(0, 128) // reserve_ton = 0
        .storeUint(0, 128) // reserve_usdt = 0
        .storeUint(0, 16) // fee_basis_points = 0
        .endCell();
}

export class SimplePool implements Contract {
    constructor(readonly address: Address, readonly init?: { code: Cell; data: Cell }) {}

    static createFromAddress(address: Address) {
        return new SimplePool(address);
    }

    static createFromConfig(config: SimplePoolConfig, code: Cell, workchain = 0) {
        const data = simplePoolConfigToCell(config);
        const init = { code, data };
        return new SimplePool(contractAddress(workchain, init), init);
    }

    async sendDeploy(provider: ContractProvider, via: Sender, value: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().endCell(),
        });
    }

    // Деплой пула (только админ)
    async sendDeployPool(
        provider: ContractProvider,
        via: Sender,
        opts: {
            usdtMaster: Address;
            feeBasisPoints: number; // например, 80 для 0.8%
            queryId?: number;
        }
    ) {
        await provider.internal(via, {
            value: toNano('0.05'),
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell()
                .storeUint(0x1, 32) // OP_DEPLOY_POOL
                .storeUint(opts.queryId ?? 0, 64)
                .storeAddress(opts.usdtMaster)
                .storeUint(opts.feeBasisPoints, 16)
                .endCell(),
        });
    }

    // Добавление ликвидности (только админ)
    async sendAddLiquidity(
        provider: ContractProvider,
        via: Sender,
        tonAmount: bigint,
        usdtAmount: bigint,
        queryId?: number
    ) {
        await provider.internal(via, {
            value: tonAmount + toNano('0.05'), // TON + газ
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell()
                .storeUint(0x2, 32) // OP_ADD_LIQUIDITY
                .storeUint(queryId ?? 0, 64)
                .storeCoins(usdtAmount)
                .endCell(),
        });
    }

    // Обмен TON на USDT
    async sendSwapTonForUsdt(
        provider: ContractProvider,
        via: Sender,
        tonAmount: bigint,
        opts: {
            minUsdtOut: bigint;
            recipient: Address;
            queryId?: number;
        }
    ) {
        await provider.internal(via, {
            value: tonAmount + toNano('0.05'), // TON + газ
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell()
                .storeUint(0x3, 32) // OP_SWAP_TON_FOR_USDT
                .storeUint(opts.queryId ?? 0, 64)
                .storeCoins(opts.minUsdtOut)
                .storeAddress(opts.recipient)
                .endCell(),
        });
    }

    // Создание payload для обмена USDT на TON (используется в USDT transfer)
    static createSwapUsdtForTonPayload(minTonOut: bigint, recipient: Address): Cell {
        return beginCell()
            .storeUint(0x4, 32) // OP_SWAP_USDT_FOR_TON
            .storeCoins(minTonOut)
            .storeAddress(recipient)
            .endCell();
    }

    // Getter методы
    async getPoolInfo(provider: ContractProvider): Promise<{
        deployed: boolean;
        admin: Address;
        usdtMaster: Address | null;
        reserveTon: bigint;
        reserveUsdt: bigint;
        feeBasisPoints: number;
    }> {
        const result = await provider.get('get_pool_info', []);
        
        const deployed = result.stack.readNumber() === 1;
        const admin = result.stack.readAddress();
        
        // Читаем USDT master - может быть пустым
        let usdtMaster: Address | null = null;
        try {
            usdtMaster = result.stack.readAddress();
        } catch (e) {
            // Адрес пустой
        }
        
        const reserveTon = result.stack.readBigNumber();
        const reserveUsdt = result.stack.readBigNumber();
        const feeBasisPoints = result.stack.readNumber();

        return {
            deployed,
            admin,
            usdtMaster,
            reserveTon,
            reserveUsdt,
            feeBasisPoints,
        };
    }

    async getReserves(provider: ContractProvider): Promise<{
        reserveTon: bigint;
        reserveUsdt: bigint;
    }> {
        const result = await provider.get('get_reserves', []);
        return {
            reserveTon: result.stack.readBigNumber(),
            reserveUsdt: result.stack.readBigNumber(),
        };
    }

    async getAmountOut(
        provider: ContractProvider,
        amountIn: bigint,
        isTonIn: boolean
    ): Promise<bigint> {
        const result = await provider.get('get_amount_out', [
            { type: 'int', value: amountIn },
            { type: 'int', value: BigInt(isTonIn ? 1 : 0) },
        ]);
        return result.stack.readBigNumber();
    }

    async getFee(provider: ContractProvider): Promise<number> {
        const result = await provider.get('get_fee', []);
        return result.stack.readNumber();
    }

    async isDeployed(provider: ContractProvider): Promise<boolean> {
        const result = await provider.get('is_deployed', []);
        return result.stack.readNumber() === 1;
    }
}